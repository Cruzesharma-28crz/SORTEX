import hashlib
import re
from pathlib import Path
from uuid import uuid4
from sortex_cloud.config import get_settings
_SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")
def dataset_dir(dataset_id: str) -> Path: return get_settings().storage_root / "datasets" / dataset_id
def save_upload(dataset_id: str, split: str, label: str, filename: str, content: bytes) -> tuple[Path, str]:
    name = _SAFE.sub("_", Path(filename).name).strip("._")[:180] or f"upload-{uuid4().hex}.jpg"
    folder = dataset_dir(dataset_id) / split / label
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4().hex}-{name}"
    path.write_bytes(content)
    return path, hashlib.sha256(content).hexdigest()
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()
