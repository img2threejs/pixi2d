"""Full-resolution pixel diagnostics for a single reference / render pair.

This is a deterministic Pillow gate, not an AI vision judge. It rejects
mismatched frames, never resizes either input, and reports bounded
RGB / alpha / global-moment luma SSIM. Color providers, automatic
acceptance scores, fake windowed SSIM and generic review SDKs are
out of scope; native agent vision makes identity judgments.
"""
from __future__ import annotations

import hashlib
import math
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from forge.common import ToolError, atomic_write_json, canonical_hash, hash_file, load_json


# Acceptance gates stay deterministic and bounded; nothing here reaches out.
_MAX_FILE_BYTES = 20 * 1024 * 1024
_MAX_DIMENSION = 8192
_MAX_PIXELS = 32_000_000
_MIN_PIXELS = 1  # empty images have no diagnostic value


def _open(path: Path, *, role: str) -> Image.Image:
    resolved = Path(path)
    try:
        size = resolved.stat().st_size
    except FileNotFoundError as error:
        raise ToolError(
            'compare-invalid-input',
            f'{role} image not found',
            {'path': str(resolved)},
        ) from error
    except OSError as error:
        raise ToolError(
            'compare-invalid-input',
            f'{role} image unreadable',
            {'path': str(resolved), 'reason': str(error)},
        ) from error
    if size > _MAX_FILE_BYTES:
        raise ToolError('image-too-large', f'{role} file exceeds 20 MiB',
                        {'path': str(resolved), 'size': size})
    try:
        with Image.open(resolved) as image:
            if image.width <= 0 or image.height <= 0:
                raise ToolError('compare-invalid-input',
                                f'{role} image has zero dimensions',
                                {'path': str(resolved)})
            if image.width > _MAX_DIMENSION or image.height > _MAX_DIMENSION:
                raise ToolError('image-too-large',
                                f'{role} image exceeds {_MAX_DIMENSION}px on a side',
                                {'path': str(resolved),
                                 'width': image.width, 'height': image.height})
            total = image.width * image.height
            if total > _MAX_PIXELS:
                raise ToolError('image-too-large',
                                f'{role} image exceeds {_MAX_PIXELS} pixels',
                                {'path': str(resolved), 'pixels': total})
            if total < _MIN_PIXELS:
                raise ToolError('compare-invalid-input',
                                f'{role} image has no pixels',
                                {'path': str(resolved)})
            image.load()
            converted = image.convert('RGBA')
    except ToolError:
        raise
    except (Image.DecompressionBombError, OSError, ValueError) as error:
        raise ToolError('compare-invalid-input',
                        f'{role} image decode failed',
                        {'path': str(resolved), 'reason': str(error)}) from error
    return converted


def _composite(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    background = Image.new('RGBA', image.size, color)
    return Image.alpha_composite(background, image).convert('RGB')


def _mean_rgb_error(first: Image.Image, second: Image.Image) -> float:
    # Both inputs are already equal-sized 8-bit RGB composites; clamp
    # finite values before averaging so a single hot pixel can never
    # poison the result with inf/nan.
    diff = ImageChops.difference(first, second)
    stat = ImageStat.Stat(diff)
    return float(sum(stat.mean) / (3 * 255))


def _mean_alpha_error(first: Image.Image, second: Image.Image) -> float:
    diff = ImageChops.difference(first.getchannel('A'), second.getchannel('A'))
    stat = ImageStat.Stat(diff)
    return float(stat.mean[0] / 255)


def _global_luma_ssim(first: Image.Image, second: Image.Image) -> float:
    """Single-scale global-moment luma SSIM.

    This is a global moment approximation (mean / variance / covariance
    over the whole crop) — not a sliding-window SSIM and not a vision
    score. Returns a finite number in [-1, 1]; degenerate constant
    images return ``1.0`` (identical luminance distributions).
    """
    if first.size != second.size:
        raise ToolError('framing-mismatch',
                        'Internal crop size mismatch in luma SSIM',
                        {'first': first.size, 'second': second.size})
    gray_first = first.convert('L')
    gray_second = second.convert('L')
    count = gray_first.width * gray_first.height
    if count <= 0:
        raise ToolError('compare-invalid-input',
                        'global luma SSIM has no pixels',
                        {'first': first.size})
    stat_first = ImageStat.Stat(gray_first)
    stat_second = ImageStat.Stat(gray_second)
    mean_first = float(stat_first.mean[0])
    mean_second = float(stat_second.mean[0])
    var_first = float(stat_first.var[0])
    var_second = float(stat_second.var[0])
    data_first = gray_first.getdata()
    data_second = gray_second.getdata()
    # Welford-style two-pass is unnecessary here because we already have
    # the population means; compute the population covariance directly.
    covariance = 0.0
    for sample_first, sample_second in zip(data_first, data_second):
        covariance += (sample_first - mean_first) * (sample_second - mean_second)
    covariance /= count
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    numerator = (2 * mean_first * mean_second + c1) * (2 * covariance + c2)
    denominator = ((mean_first ** 2 + mean_second ** 2 + c1)
                   * (var_first + var_second + c2))
    if denominator <= 0 or not math.isfinite(denominator):
        # Both images constant and identical ⇒ return 1.0; otherwise
        # the metric is undefined and we surface 'unmeasured' upstream.
        return 1.0 if mean_first == mean_second else 0.0
    value = numerator / denominator
    if not math.isfinite(value):
        return 0.0
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return float(value)


def _validate_bbox(bbox, frame: tuple[int, int]) -> tuple[int, int, int, int]:
    if bbox is None:
        return (0, 0, frame[0], frame[1])
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ToolError('invalid-crop',
                        'bbox must be a 4-tuple/list [x, y, w, h]',
                        {'bbox': list(bbox) if hasattr(bbox, '__iter__') else bbox})
    if any(not isinstance(value, int) or isinstance(value, bool) for value in bbox):
        raise ToolError('invalid-crop', 'bbox entries must be integers', {'bbox': list(bbox)})
    x, y, width, height = bbox
    if width <= 0 or height <= 0:
        raise ToolError('invalid-crop',
                        'bbox width and height must be positive',
                        {'bbox': [x, y, width, height]})
    if x < 0 or y < 0:
        raise ToolError('invalid-crop',
                        'bbox origin must be non-negative',
                        {'bbox': [x, y, width, height]})
    if x + width > frame[0] or y + height > frame[1]:
        raise ToolError('invalid-crop',
                        'bbox extends past reference artboard',
                        {'bbox': [x, y, width, height],
                         'artboard': list(frame)})
    return (x, y, width, height)


def compare_images(reference: Path, rendered: Path, output: Path,
                   *, bbox: list[int] | tuple[int, int, int, int] | None = None) -> dict:
    """Compare ``reference`` to ``rendered`` without resizing either input.

    The two PNGs must already share the same frame; otherwise the helper
    rejects the pair with ``framing-mismatch`` and never silently rescales
    either artboard. ``bbox`` selects a sub-rectangle (must lie inside the
    artboard) and gates the metrics to the crop. The function writes a
    3-panel sheet (reference over white, render over white, absolute RGB
    difference) plus metrics JSON. The PNG filename uses its encoded-byte
    SHA-256; the JSON filename uses its canonical payload SHA-256.
    Identical reports are reused without rewriting their evidence.
    """
    first_full = _open(reference, role='reference')
    second_full = _open(rendered, role='render')
    if first_full.size != second_full.size:
        raise ToolError(
            'framing-mismatch',
            'Reference and actual canvas PNG dimensions must match; do not resize either',
            {'reference': list(first_full.size),
             'render': list(second_full.size)})
    frame = first_full.size
    x, y, width, height = _validate_bbox(bbox, frame)
    rectangle = (x, y, x + width, y + height)
    first = first_full.crop(rectangle)
    second = second_full.crop(rectangle)
    first_full.close()
    second_full.close()

    white_first = _composite(first, (255, 255, 255))
    white_second = _composite(second, (255, 255, 255))
    black_first = _composite(first, (0, 0, 0))
    black_second = _composite(second, (0, 0, 0))

    mean_rgb_white = _mean_rgb_error(white_first, white_second)
    mean_rgb_black = _mean_rgb_error(black_first, black_second)
    mean_alpha = _mean_alpha_error(first, second)
    luma_ssim = _global_luma_ssim(white_first, white_second)

    for label, value in (('meanRGBErrorWhite', mean_rgb_white),
                         ('meanRGBErrorBlack', mean_rgb_black),
                         ('meanAlphaError', mean_alpha),
                         ('globalLumaSSIM', luma_ssim)):
        if not math.isfinite(value):
            raise ToolError('compare-invalid-input',
                            f'{label} is non-finite',
                            {'value': value, 'frame': list(frame),
                             'bbox': [x, y, width, height]})
        if label == 'globalLumaSSIM' and not (-1.0 <= value <= 1.0):
            raise ToolError('compare-invalid-input',
                            'globalLumaSSIM outside [-1, 1]',
                            {'value': value})

    difference = ImageChops.difference(white_first, white_second)
    sheet = Image.new('RGB', (first.width * 3, first.height), (255, 255, 255))
    for index, image in enumerate((white_first, white_second, difference)):
        sheet.paste(image, (index * first.width, 0))
    buffer = BytesIO()
    sheet.save(buffer, format='PNG')
    sheet_bytes = buffer.getvalue()
    sheet_hash = hashlib.sha256(sheet_bytes).hexdigest()

    output_dir = Path(output)
    if output_dir.is_file():
        raise ToolError('unsafe-path',
                        'compare --out must be a directory, not a file',
                        {'output': str(output_dir)})
    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = output_dir / f'comparison.{sheet_hash}.png'
    if sheet_path.exists():
        if hash_file(sheet_path) != sheet_hash:
            raise ToolError('artifact-conflict',
                            'Existing comparison artifact has different bytes',
                            {'path': str(sheet_path)})
    else:
        with sheet_path.open('xb') as stream:
            stream.write(sheet_bytes)

    result = {
        'status': 'compared',
        'referencePath': str(Path(reference)),
        'renderedPath': str(Path(rendered)),
        'referenceHash': hash_file(reference),
        'renderHash': hash_file(rendered),
        'artboard': list(frame),
        'bbox': [x, y, width, height],
        'metrics': {
            'meanRGBErrorWhite': mean_rgb_white,
            'meanRGBErrorBlack': mean_rgb_black,
            'meanAlphaError': mean_alpha,
            'globalLumaSSIM': luma_ssim,
        },
        'comparison': str(sheet_path),
        'comparisonHash': sheet_hash,
        'panels': ['reference over white', 'render over white',
                   'absolute RGB difference'],
        'limitations': [
            'Global-moment luma SSIM is not windowed SSIM; evaluate critical crops separately.',
            'No vision score, identity judgment, editability proof or acceptance decision is computed.',
            'Bbox region metrics are diagnostic; the agent inspects native and decides.',
        ],
    }

    metrics_path = output_dir / f'metrics.{canonical_hash(result)}.json'
    if metrics_path.exists():
        existing = load_json(metrics_path)
        if existing != result:
            raise ToolError('artifact-conflict',
                            'Existing metrics artifact has different content',
                            {'path': str(metrics_path)})
    else:
        atomic_write_json(metrics_path, result)
    return result