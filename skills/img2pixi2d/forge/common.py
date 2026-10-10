from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

class ToolError(Exception):
    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code, self.details = code, details
    def as_dict(self) -> dict[str, Any]:
        return {"status": "error", "code": self.code, "message": str(self), "details": self.details}

def hash_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def atomic_write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + target.name, dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def safe_path(root: str | Path, relative: str) -> Path:
    base = Path(root).resolve()
    if Path(relative).is_absolute():
        raise ToolError('unsafe-path', 'Expected a workspace-relative path', relative)
    result = (base / relative).resolve()
    if not result.is_relative_to(base):
        raise ToolError('unsafe-path', 'Path escapes workspace', relative)
    return result

def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ToolError('invalid-json', str(error), str(path)) from error
