import hashlib
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from sortex_cloud.config import get_settings

_SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")


def dataset_dir(dataset_id: str) -> Path:
    return get_settings().storage_root / "datasets" / dataset_id


def _storage_request(method: str, object_key: str, content: bytes | None = None, content_type: str = "application/octet-stream") -> bytes:
    settings = get_settings()
    if not settings.use_supabase_storage:
        raise RuntimeError("Supabase Storage is not configured")
    bucket = quote(settings.storage_bucket, safe="")
    key = quote(object_key.lstrip("/"), safe="/")
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{key}"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": content_type,
    }
    request = Request(url, data=content, headers=headers, method=method)
    try:
        with urlopen(request, timeout=90) as response:
            return response.read()
    except HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase Storage request failed ({exc.code}): {detail}") from exc


def save_upload(dataset_id: str, split: str, label: str, filename: str, content: bytes) -> tuple[str, str]:
    name = _SAFE.sub("_", Path(filename).name).strip("._")[:180] or f"upload-{uuid4().hex}.jpg"
    object_key = f"datasets/{dataset_id}/{split}/{label}/{uuid4().hex}-{name}"
    checksum = hashlib.sha256(content).hexdigest()
    settings = get_settings()
    if settings.use_supabase_storage:
        suffix = Path(name).suffix.lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(suffix, "application/octet-stream")
        _storage_request("POST", object_key, content, mime)
    else:
        path = dataset_dir(dataset_id) / split / label / Path(object_key).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return object_key, checksum


def download_object(object_key: str, destination: Path) -> Path:
    settings = get_settings()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if settings.use_supabase_storage:
        destination.write_bytes(_storage_request("GET", object_key))
    else:
        source = settings.storage_root / object_key
        if not source.is_file():
            raise FileNotFoundError(object_key)
        destination.write_bytes(source.read_bytes())
    return destination


def read_object(object_key: str) -> bytes:
    settings = get_settings()
    if settings.use_supabase_storage:
        return _storage_request("GET", object_key)
    path = settings.storage_root / object_key
    if not path.is_file():
        raise FileNotFoundError(object_key)
    return path.read_bytes()


def save_model_bundle(local_path: Path, job_id: str) -> str:
    object_key = f"models/{job_id}/{local_path.name}"
    settings = get_settings()
    if settings.use_supabase_storage:
        _storage_request("POST", object_key, local_path.read_bytes(), "application/zip")
    else:
        destination = settings.storage_root / object_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(local_path.read_bytes())
    return object_key


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
