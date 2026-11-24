import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import requests
from sortex.inference import predict

def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): value.update(chunk)
    return value.hexdigest()

def sync(api_url: str, api_key: str, model_dir: Path) -> dict:
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{api_url.rstrip('/')}/v1/devices/model", headers=headers, timeout=30)
    response.raise_for_status(); manifest = response.json()
    if not manifest.get("available"): return manifest
    current = model_dir / "current.json"
    if current.exists() and json.loads(current.read_text(encoding="utf-8")).get("model_id") == manifest["model_id"]:
        return {"updated": False, "version": manifest["version"]}
    response = requests.get(f"{api_url.rstrip('/')}{manifest['download_path']}", headers=headers, timeout=180)
    response.raise_for_status(); model_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=model_dir, suffix=".zip", delete=False) as temp:
        temp.write(response.content); archive_path = Path(temp.name)
    try:
        if digest(archive_path) != manifest["sha256"]: raise ValueError("Model checksum mismatch")
        staging = model_dir / ".staging"
        if staging.exists(): shutil.rmtree(staging)
        staging.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for item in archive.infolist():
                target = (staging / item.filename).resolve()
                if staging.resolve() not in target.parents: raise ValueError("Unsafe model bundle path")
            archive.extractall(staging)
        metadata = json.loads((staging / "metadata.json").read_text(encoding="utf-8"))
        if metadata.get("model_version") != manifest["version"]: raise ValueError("Model version mismatch")
        active = model_dir / manifest["version"]
        if active.exists(): shutil.rmtree(active)
        staging.replace(active)
        current.write_text(json.dumps({"model_id": manifest["model_id"], "version": manifest["version"], "checkpoint": str(active / "model.pt")}, indent=2), encoding="utf-8")
        return {"updated": True, "version": manifest["version"]}
    finally: archive_path.unlink(missing_ok=True)

def main() -> None:
    parser = argparse.ArgumentParser(prog="sortex-edge")
    commands = parser.add_subparsers(dest="command", required=True)
    sync_parser = commands.add_parser("sync"); sync_parser.add_argument("--api-url", default=os.getenv("SORTEX_API_URL", "")); sync_parser.add_argument("--api-key", default=os.getenv("SORTEX_DEVICE_API_KEY", "")); sync_parser.add_argument("--model-dir", type=Path, default=Path("./models"))
    pred = commands.add_parser("predict"); pred.add_argument("image"); pred.add_argument("--model-dir", type=Path, default=Path("./models"))
    args = parser.parse_args()
    if args.command == "sync":
        if not args.api_url or not args.api_key: parser.error("Set SORTEX_API_URL and SORTEX_DEVICE_API_KEY or pass both")
        print(json.dumps(sync(args.api_url, args.api_key, args.model_dir), indent=2))
    else:
        state = json.loads((args.model_dir / "current.json").read_text(encoding="utf-8"))
        print(json.dumps(predict(args.image, state["checkpoint"]), indent=2))

if __name__ == "__main__": main()
