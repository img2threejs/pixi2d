"""Alpha-preserving extraction, never automatic segmentation."""
from io import BytesIO
from pathlib import Path
import hashlib
from PIL import Image, ImageChops
from forge.common import ToolError, atomic_write_json, hash_file, load_json, safe_path


def crop_reference(workspace: Path, bbox: list[int], output: str, *, mask: str | None = None) -> dict:
    workspace = Path(workspace).resolve()
    admission = load_json(workspace / 'intake.json')
    reference = admission['reference']
    source = safe_path(workspace, reference['src'])
    if admission['status'] != 'proceed' or hash_file(source) != reference['sha256']:
        raise ToolError('stale-reference', 'Admitted reference bytes have changed')
    x, y, width, height = bbox
    if min(x, y) < 0 or min(width, height) <= 0 or x + width > reference['width'] or y + height > reference['height']:
        raise ToolError('invalid-crop', 'Crop must be a nonempty rectangle inside the working reference')
    destination = safe_path(workspace, output)
    if destination.suffix.lower() != '.png':
        raise ToolError('invalid-output', 'Layer output must be PNG')
    metadata_path = safe_path(workspace, str(destination.with_suffix('.meta.json').relative_to(workspace)))
    mask_path = safe_path(workspace, mask) if mask else None
    if metadata_path == destination or (metadata_path.exists() and destination.exists() and metadata_path.samefile(destination)):
        raise ToolError('invalid-output', 'Layer and provenance outputs must be distinct')
    relative = destination.relative_to(workspace)
    inputs = [source, workspace / 'intake.json']
    if reference.get('originalSrc'):
        inputs.append(safe_path(workspace, reference['originalSrc']))
    if mask_path is not None:
        inputs.append(mask_path)
    for path in (destination, metadata_path):
        if path == workspace or path.relative_to(workspace).parts[0] == 'reference':
            raise ToolError('immutable-reference', 'Write derived layers outside the immutable reference directory')
        if any(path == item or (path.exists() and item.exists() and path.samefile(item)) for item in inputs):
            raise ToolError('immutable-reference', 'Layer and provenance outputs must not replace inputs', str(path))
    with Image.open(source) as image:
        layer = image.convert('RGBA').crop((x, y, x + width, y + height))
    mask_hash = None
    if mask_path is not None:
        if mask_path.stat().st_size > 20 * 1024 * 1024:
            raise ToolError('invalid-mask', 'Matte exceeds 20 MiB')
        with Image.open(mask_path) as image:
            if image.width > 8192 or image.height > 8192 or image.width * image.height > 32_000_000:
                raise ToolError('invalid-mask', 'Matte exceeds decoded dimension limits')
            if image.size == (reference['width'], reference['height']):
                image = image.crop((x, y, x + width, y + height))
            elif image.size != (width, height):
                raise ToolError('invalid-mask', 'Matte must match the exact crop or full-reference registration; no resize')
            if 'A' in image.getbands():
                matte = image.getchannel('A')
            elif 'transparency' in image.info:
                matte = image.convert('RGBA').getchannel('A')
            else:
                matte = image.convert('L')
            layer.putalpha(ImageChops.multiply(layer.getchannel('A'), matte))
        mask_hash = hash_file(mask_path)
    bounds = layer.getchannel('A').getbbox()
    if bounds is None:
        raise ToolError('empty-layer', 'Crop/matte contains no visible pixels')
    trimmed = layer.crop(bounds)
    buffer = BytesIO()
    trimmed.save(buffer, format='PNG')
    data = buffer.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    metadata = {'status': 'ready', 'src': relative.as_posix(), 'sha256': digest,
                'referenceHash': reference['sha256'], 'crop': bbox,
                'originalWidth': width, 'originalHeight': height,
                'width': trimmed.width, 'height': trimmed.height,
                'trimOffset': [bounds[0], bounds[1]]}
    if mask:
        metadata.update(mask=mask, maskHash=mask_hash)
    metadata_exists = metadata_path.exists()
    if metadata_exists and (not metadata_path.is_file() or load_json(metadata_path) != metadata):
        raise ToolError('output-exists', 'Refusing to replace different layer provenance', str(metadata_path))
    if destination.exists() and (not destination.is_file() or hash_file(destination) != digest):
        raise ToolError('output-exists', 'Refusing to overwrite a different layer', output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open('xb') as stream:
            stream.write(data)
    except FileExistsError:
        if not destination.is_file() or hash_file(destination) != digest:
            raise ToolError('output-exists', 'Refusing to overwrite a different layer', output)
    if not metadata_exists:
        atomic_write_json(metadata_path, metadata)
    return metadata
