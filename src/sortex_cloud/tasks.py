import json
import shutil
import zipfile
from datetime import datetime, timezone
from sortex_cloud.config import get_settings
from sortex_cloud.database import Dataset, ModelVersion, SessionLocal, TrainingJob
from sortex_cloud.queue import celery_app
from sortex_cloud.storage import dataset_dir, sha256_file
@celery_app.task(name="sortex.train_dataset")
def train_dataset(job_id: str) -> dict:
    from sortex.evaluation import evaluate
    from sortex.training import train
    settings = get_settings()
    with SessionLocal() as db:
        job = db.get(TrainingJob, job_id)
        if job is None: raise ValueError("Training job does not exist")
        dataset = db.get(Dataset, job.dataset_id)
        if dataset is None: raise ValueError("Dataset does not exist")
        job.status = "running"; db.commit()
        dataset_id, epochs, batch_size = dataset.id, job.epochs, job.batch_size
    root = dataset_dir(dataset_id)
    output = settings.storage_root / "models"; output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / f"{job_id}.pt"
    try:
        train(str(root), str(checkpoint), epochs=epochs, batch_size=batch_size)
        has_test = all(any((root / "test" / label).glob("*")) for label in ("dry_waste", "e_waste", "wet_waste"))\n        metrics = evaluate(str(root / "test"), str(checkpoint)) if has_test else {}
        version = f"0.1.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{job_id[:8]}"
        folder = output / job_id; folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checkpoint, folder / "model.pt")
        metadata = {"format_version": 1, "sortex_version": "0.1.0", "model_version": version, "classes": ["dry_waste", "e_waste", "wet_waste"], "image_size": 160, "normalization": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}, "confidence_threshold": settings.model_confidence_threshold, "metrics": metrics}
        (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (folder / "labels.json").write_text(json.dumps(metadata["classes"], indent=2), encoding="utf-8")
        bundle = output / f"{job_id}.zip"
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in folder.iterdir(): archive.write(item, item.name)
        with SessionLocal() as db:
            job = db.get(TrainingJob, job_id)
            model = ModelVersion(version=version, dataset_id=dataset_id, job_id=job_id, status="pending_review", bundle_path=str(bundle), sha256=sha256_file(bundle), metrics_json=json.dumps(metrics))
            db.add(model); db.flush(); job.status, job.model_id = "completed", model.id; db.commit()
        return {"job_id": job_id, "model_version": version, "status": "pending_review"}
    except Exception as exc:
        with SessionLocal() as db:
            job = db.get(TrainingJob, job_id)
            if job: job.status, job.error = "failed", str(exc)[:4000]; db.commit()
        raise
