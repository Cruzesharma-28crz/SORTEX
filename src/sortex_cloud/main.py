import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sortex.labels import CLASSES, validate_class
from sortex_cloud.auth import Principal, admin, contributor, device, trainer
from sortex_cloud.config import get_settings
from sortex_cloud.database import Dataset, ImageRecord, ModelVersion, SessionLocal, TrainingJob, init_db
from sortex_cloud.queue import celery_app
from sortex_cloud.storage import dataset_dir, save_upload
app = FastAPI(title="SORTEX Cloud API", version="0.1.0")
@app.on_event("startup")
def startup() -> None: init_db()
class DatasetCreate(BaseModel): name: str = Field(min_length=2, max_length=120)
class TrainingCreate(BaseModel):
    dataset_id: str
    epochs: int = Field(default=30, ge=1, le=200)
    batch_size: int = Field(default=32, ge=1, le=256)
@app.get("/health")
def health() -> dict: return {"status": "ok", "service": "sortex-cloud-api", "version": "0.1.0"}
@app.get("/v1/classes")
def classes() -> dict: return {"classes": list(CLASSES)}
@app.post("/v1/datasets", status_code=201)
def create_dataset(payload: DatasetCreate, principal: Principal = Depends(contributor)) -> dict:
    with SessionLocal() as db:
        row = Dataset(name=payload.name, owner=principal.owner); db.add(row); db.commit(); db.refresh(row)
        for split in ("train", "val", "test"):
            for label in CLASSES: (dataset_dir(row.id) / split / label).mkdir(parents=True, exist_ok=True)
        return {"id": row.id, "name": row.name, "owner": row.owner}
@app.post("/v1/datasets/{dataset_id}/images", status_code=201)
async def upload_image(dataset_id: str, label: str, file: UploadFile = File(...), split: str = "train", principal: Principal = Depends(contributor)) -> dict:
    try: validate_class(label)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    if split not in {"train", "val", "test"}: raise HTTPException(status_code=422, detail="Invalid dataset split")
    settings = get_settings(); content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if not content or len(content) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(status_code=413, detail="Image is empty or exceeds upload limit")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP images are accepted")
    try:
        import io
        from PIL import Image
        with Image.open(io.BytesIO(content)) as image: image.verify()
    except Exception as exc: raise HTTPException(status_code=422, detail="Invalid image file") from exc
    with SessionLocal() as db:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None: raise HTTPException(status_code=404, detail="Dataset not found")
        if dataset.owner != principal.owner and principal.role not in {"admin", "trainer"}: raise HTTPException(status_code=403, detail="Dataset belongs to another contributor")
        path, checksum = save_upload(dataset_id, split, label, file.filename or "image.jpg", content)
        record = ImageRecord(dataset_id=dataset_id, label=label, split=split, filename=path.name, path=str(path), uploader=principal.owner)
        db.add(record); db.commit()
        return {"id": record.id, "label": label, "split": split, "sha256": checksum}
@app.get("/v1/datasets")
def list_datasets(principal: Principal = Depends(contributor)) -> list[dict]:
    with SessionLocal() as db:
        query = select(Dataset) if principal.role in {"trainer", "admin"} else select(Dataset).where(Dataset.owner == principal.owner)
        rows = db.scalars(query).all()
        return [{"id": row.id, "name": row.name, "created_at": row.created_at.isoformat()} for row in rows]
@app.post("/v1/training", status_code=202)
def start_training(payload: TrainingCreate, principal: Principal = Depends(trainer)) -> dict:
    with SessionLocal() as db:
        dataset = db.get(Dataset, payload.dataset_id)
        if dataset is None: raise HTTPException(status_code=404, detail="Dataset not found")
        if dataset.owner != principal.owner and principal.role not in {"admin", "trainer"}: raise HTTPException(status_code=403, detail="Dataset belongs to another contributor")
        root = dataset_dir(dataset.id)
        missing = [f"{part}/{label}" for part in ("train", "val") for label in CLASSES if not any((root / part / label).glob("*"))]
        if missing: raise HTTPException(status_code=422, detail=f"Missing images in: {', '.join(missing)}")
        job = TrainingJob(dataset_id=dataset.id, status="queued", epochs=payload.epochs, batch_size=payload.batch_size, created_by=principal.owner)
        db.add(job); db.commit(); db.refresh(job); celery_app.send_task("sortex.train_dataset", args=[job.id])
        return {"job_id": job.id, "status": job.status}
@app.get("/v1/training/{job_id}")
def training_status(job_id: str, principal: Principal = Depends(trainer)) -> dict:
    with SessionLocal() as db:
        job = db.get(TrainingJob, job_id)
        if job is None: raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job.id, "status": job.status, "error": job.error, "model_id": job.model_id}
@app.get("/v1/models")
def list_models(principal: Principal = Depends(trainer)) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(select(ModelVersion).order_by(ModelVersion.created_at.desc())).all()
        return [{"id": row.id, "version": row.version, "status": row.status, "sha256": row.sha256, "metrics": json.loads(row.metrics_json)} for row in rows]
@app.post("/v1/models/{model_id}/approve")
def approve_model(model_id: str, principal: Principal = Depends(admin)) -> dict:
    with SessionLocal() as db:
        model = db.get(ModelVersion, model_id)
        if model is None: raise HTTPException(status_code=404, detail="Model not found")
        if model.status != "pending_review": raise HTTPException(status_code=409, detail="Model is not pending review")
        for old in db.scalars(select(ModelVersion).where(ModelVersion.status == "approved")).all(): old.status = "retired"
        model.status, model.approved_at = "approved", datetime.now(timezone.utc); db.commit()
        return {"id": model.id, "version": model.version, "status": model.status}
@app.get("/v1/devices/model")
def device_model(principal: Principal = Depends(device)) -> dict:
    with SessionLocal() as db:
        model = db.scalar(select(ModelVersion).where(ModelVersion.status == "approved").order_by(ModelVersion.approved_at.desc()))
        if model is None: return {"available": False}
        return {"available": True, "model_id": model.id, "version": model.version, "sha256": model.sha256, "download_path": f"/v1/devices/models/{model.id}/download"}
@app.get("/v1/devices/models/{model_id}/download")
def download_model(model_id: str, principal: Principal = Depends(device)) -> FileResponse:
    with SessionLocal() as db:
        model = db.get(ModelVersion, model_id)
        if model is None or model.status != "approved": raise HTTPException(status_code=404, detail="Approved model not found")
        path = Path(model.bundle_path)
        if not path.is_file(): raise HTTPException(status_code=410, detail="Bundle unavailable")
        return FileResponse(path, filename=f"sortex-{model.version}.zip", media_type="application/zip")


portal_dir = Path(__file__).resolve().parents[2] / "portal"
if portal_dir.is_dir():
    app.mount("/portal", StaticFiles(directory=portal_dir, html=True), name="portal")
