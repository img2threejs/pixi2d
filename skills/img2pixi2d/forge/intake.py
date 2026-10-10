from __future__ import annotations

import hashlib
import http.client
import io
import ipaddress
import json
import os
import shutil
import socket
import ssl
import tempfile
import threading
import time
import warnings
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

from forge.common import ToolError, atomic_write_json, hash_file

MAX_BYTES = 20 * 1024 * 1024
MAX_EDGE = 8192
MAX_PIXELS = 32_000_000
FORMATS = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp', 'BMP': 'bmp', 'TIFF': 'tif', 'GIF': 'gif'}


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, timeout: float):
        super().__init__(host, 443, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self) -> None:
        transport = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(transport, server_hostname=self.host)
        except BaseException:
            transport.close()
            raise


def _public_address(value: str) -> bool:
    address = ipaddress.ip_address(value.split('%')[0])
    if getattr(address, 'ipv4_mapped', None) is not None:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast
def _dns_answers(host: str, timeout: float) -> list:
    """Bound caller latency even when the platform resolver is stalled."""
    import queue
    result: queue.Queue = queue.Queue(maxsize=1)
    def resolve() -> None:
        try:
            result.put((True, socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
        except OSError as error:
            result.put((False, error))
    threading.Thread(target=resolve, daemon=True).start()
    try:
        succeeded, value = result.get(timeout=max(0, timeout))
    except queue.Empty as error:
        raise ToolError('dns-timeout', 'Reference DNS resolution exceeded its deadline') from error
    if not succeeded:
        raise ToolError('dns-failed', str(value)) from value
    return value


def _resolve_url(url: str, *, timeout: float = 10) -> tuple[str, str, str]:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ToolError('unsafe-url', 'Invalid URL port') from exc
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None or parsed.password is not None or port not in (None, 443):
        raise ToolError('unsafe-url', 'Only credential-free HTTPS URLs on port 443 are allowed')
    host = parsed.hostname.encode('idna').decode('ascii')
    if host.lower().rstrip('.') in {'localhost', 'localhost.localdomain'}:
        raise ToolError('private-address', 'Private network input is forbidden')
    answers = _dns_answers(host, timeout)
    addresses = sorted({answer[4][0] for answer in answers})
    if not addresses or not all(_public_address(address) for address in addresses):
        raise ToolError('private-address', 'Every resolved address must be public', addresses)
    return host, addresses[0], (parsed.path or '/') + ('?' + parsed.query if parsed.query else '')


def _socket_deadline(transport: socket.socket, deadline: float) -> threading.Timer:
    """Interrupt socket I/O even when a peer keeps sending partial headers/body."""
    def expire() -> None:
        try:
            transport.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass  # The peer or caller may already have disconnected.
        # Closing here can remove the descriptor before a Darwin poll wakes.
        # The I/O owner closes it after the interrupted operation returns.
    timer = threading.Timer(max(0, deadline - time.monotonic()), expire)
    timer.daemon = True
    timer.start()
    return timer


def _download(url: str) -> bytes:
    deadline = time.monotonic() + 30
    for _ in range(6):
        host, address, target = _resolve_url(url, timeout=min(10, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
        connection = _PinnedHTTPS(host, address, min(10, remaining))
        guard = None
        response = None
        transport = None
        try:
            connection.connect()
            transport = connection.sock
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
            guard = _socket_deadline(transport, deadline)
            transport.settimeout(min(10, remaining))
            connection.request('GET', target, headers={'Accept': 'image/*', 'User-Agent': 'img2pixi2d/1.0'})
            transport.settimeout(min(10, max(0.001, deadline - time.monotonic())))
            response = connection.getresponse()
            if time.monotonic() >= deadline:
                raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader('Location')
                if not location:
                    raise ToolError('invalid-redirect', 'Redirect without Location')
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise ToolError('http-error', f'Reference server returned HTTP {response.status}')
            content_type = (response.getheader('Content-Type') or '').split(';')[0].strip().lower()
            if content_type == 'image/svg+xml' or (content_type and not content_type.startswith('image/')):
                raise ToolError('unsupported-mime', 'Expected a passive raster image', content_type)
            size = response.getheader('Content-Length')
            if size:
                try:
                    if int(size) > MAX_BYTES:
                        raise ToolError('image-too-large', 'Reference exceeds 20 MiB')
                except ValueError as exc:
                    raise ToolError('invalid-length', 'Invalid Content-Length') from exc
            chunks, length = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
                transport.settimeout(min(10, remaining))
                chunk = response.read(min(65536, MAX_BYTES + 1 - length))
                if time.monotonic() >= deadline:
                    raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
                if length > MAX_BYTES:
                    raise ToolError('image-too-large', 'Reference exceeds 20 MiB')
            data = b''.join(chunks)
            if time.monotonic() >= deadline:
                raise ToolError('download-timeout', 'Reference download exceeded 30 seconds')
            return data
        except (OSError, ValueError, http.client.HTTPException) as error:
            if time.monotonic() >= deadline:
                raise ToolError('download-timeout', 'Reference download exceeded 30 seconds') from error
            raise
        finally:
            if guard is not None:
                guard.cancel()
                guard.join()
            if response is not None:
                response.close()
            connection.close()
            if transport is not None:
                transport.close()
    raise ToolError('redirect-limit', 'Reference exceeded five redirects')


def _normalize(data: bytes) -> tuple[Image.Image, dict]:
    if len(data) > MAX_BYTES:
        raise ToolError('image-too-large', 'Reference exceeds 20 MiB')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            width, height = probe.size
            if fmt not in FORMATS:
                raise ToolError('unsupported-format', 'Only passive raster formats are supported', fmt)
            if max(width, height) > MAX_EDGE or width * height > MAX_PIXELS:
                raise ToolError('image-dimensions', 'Reference exceeds 8192px edge or 32 megapixels', [width, height])
            if getattr(probe, 'n_frames', 1) != 1:
                raise ToolError('animated-reference', 'Supply a single reference frame instead of an animation')
            probe.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            orientation = image.getexif().get(274, 1)
            profile = image.info.get('icc_profile')
            normalized = ImageOps.exif_transpose(image)
            alpha = normalized.convert('RGBA').getchannel('A')
            if profile:
                try:
                    source_profile = ImageCms.ImageCmsProfile(io.BytesIO(profile))
                    target_profile = ImageCms.createProfile('sRGB')
                    mode = normalized.mode if normalized.mode in {'RGB', 'CMYK', 'LAB', 'L'} else 'RGB'
                    color = ImageCms.profileToProfile(normalized.convert(mode), source_profile, target_profile, outputMode='RGB')
                except (ValueError, OSError, ImageCms.PyCMSError) as exc:
                    raise ToolError('invalid-color-profile', 'ICC conversion failed; source color cannot be silently changed') from exc
            else:
                color = normalized.convert('RGB')
            result = color.convert('RGBA')
            result.putalpha(alpha)
            return result, {'format': fmt, 'orientation': orientation, 'colorProfile': 'converted-to-sRGB' if profile else 'assumed-sRGB-no-profile', 'alpha': alpha.getextrema()[0] < 255, 'originalDimensions': [width, height]}


def intake_reference(source: str, workspace: Path, *, allow_network: bool = False) -> dict:
    try:
        workspace = Path(workspace).resolve()
        scheme = urlsplit(source).scheme.lower()
        if scheme:
            if not allow_network:
                raise ToolError('network-consent-required', 'HTTPS download requires --allow-network')
            data = _download(source)
        else:
            path = Path(source).expanduser().resolve()
            if not path.is_file():
                raise ToolError('missing-reference', 'Reference is not a readable local file', str(path))
            if path.stat().st_size > MAX_BYTES:
                raise ToolError('image-too-large', 'Reference exceeds 20 MiB')
            with path.open('rb') as stream:
                data = stream.read(MAX_BYTES + 1)
        image, metadata = _normalize(data)
        original_hash = hashlib.sha256(data).hexdigest()
        workspace.mkdir(parents=True, exist_ok=True)
        reference_dir = workspace / 'reference'
        original_name = 'original.' + FORMATS[metadata['format']]
        result = {'status': 'proceed', 'reference': {'src': 'reference/working.png', 'sha256': None, 'width': image.width, 'height': image.height, 'originalSrc': 'reference/' + original_name, 'originalHash': original_hash}, 'metadata': metadata, 'issues': []}
        existing = reference_dir / original_name
        intake_path = workspace / 'intake.json'
        if reference_dir.exists() or reference_dir.is_symlink() or intake_path.exists() or intake_path.is_symlink():
            working = reference_dir / 'working.png'
            if not any(path.is_symlink() for path in (reference_dir, existing, working, intake_path)) and existing.is_file() and hash_file(existing) == original_hash and intake_path.is_file() and working.is_file():
                try:
                    previous = json.loads(intake_path.read_text())
                except ValueError as error:
                    raise ToolError('reference-exists', 'Existing intake metadata is invalid; preserve it and use a new workspace') from error
                result['reference']['sha256'] = hash_file(working)
                if previous == result:
                    return previous
            raise ToolError('reference-exists', 'Use a new workspace for a different reference; original is immutable')
        stage = Path(tempfile.mkdtemp(prefix='.reference-', dir=workspace))
        try:
            (stage / original_name).write_bytes(data)
            image.save(stage / 'working.png', format='PNG')
            working_hash = hash_file(stage / 'working.png')
            os.replace(stage, reference_dir)
        finally:
            if stage.exists(): shutil.rmtree(stage)
        result['reference']['sha256'] = working_hash
        atomic_write_json(workspace / 'intake.json', result)
        return result
    except ToolError as error:
        status = 'request-input' if error.code in {'network-consent-required', 'missing-reference', 'reference-exists'} else ('unsupported' if error.code in {'unsupported-format', 'unsupported-mime', 'animated-reference'} else 'rejected')
        return {'status': status, 'reference': None, 'metadata': {}, 'issues': [error.as_dict()]}
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, http.client.HTTPException) as error:
        return {'status': 'rejected', 'reference': None, 'metadata': {}, 'issues': [{'code': 'decode-or-fetch-failed', 'message': str(error)}]}
