# SORTEX

SORTEX is a hybrid cloud-edge waste-classification research platform. The cloud collects and manages datasets, trains and evaluates the custom CNN, and publishes approved model bundles. A Raspberry Pi downloads approved bundles and performs local inference offline.

**Current status:** cloud API, dataset intake, asynchronous training pipeline, model review and edge client are implemented. Cloud deployment requires the environment variables below and a Render worker. No dataset or trained weights are included, and camera transport or physical actuation is not implemented.

## Architecture

- **Render Web Service:** FastAPI API and browser portal.
- **Supabase PostgreSQL:** dataset, image, job and model metadata.
- **Supabase Storage:** private image datasets and model bundles.
- **Render Key Value:** Redis-compatible Celery queue.
- **Render Background Worker:** isolated PyTorch CPU training and evaluation.
- **Raspberry Pi:** downloads approved model bundles and performs local inference offline.

## Cloud configuration

Configure these values as server-side environment variables on both the API and worker services:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase PostgreSQL session-pooler connection string, with SSL enabled |
| `REDIS_URL` | Render Key Value connection string |
| `SUPABASE_URL` | Project API URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Legacy server-only service_role JWT for private Storage operations |
| `STORAGE_BUCKET` | Private bucket name, defaults to `sortex-assets` |
| `SORTEX_API_KEYS_JSON` | Server-side contributor, trainer, admin and device API keys |
| `MAX_UPLOAD_MB` | Per-image upload limit, defaults to 12 |
| `MODEL_CONFIDENCE_THRESHOLD` | Metadata threshold, defaults to 0.65 |

Never put the Supabase service-role key or trainer/admin/device API keys in the browser portal, public repository, or client devices other than the device-scoped key on the Pi. Use the Supabase **Session pooler** connection string (port 5432) for SQLAlchemy, and add `sslmode=require`. Do not use the transaction pooler for this application.

The `sortex-assets` bucket must remain private. The API and worker use the server-side Storage credential; no public Storage policies are required. Public-schema metadata tables have row-level security enabled and no browser access policies.

## Render deployment

A Render Blueprint is provided in `render.yaml`. It defines:
- Free web API service for prototype access.
- Background worker (starter compute) for small CPU training jobs.
- Free Key Value for the Celery queue.

Render does not offer free background workers. The worker plan currently uses the smallest paid worker tier; check the Render dashboard plan before approving a Blueprint sync. The free Key Value instance is in-memory and may lose queued jobs on restart, so it is for prototyping only. Upgrade to persistent Key Value before relying on unattended training.

## Dataset format

Each dataset has three splits and three exact class folder names:

```
dataset/
  train/
    dry_waste/
    e_waste/
    wet_waste/
  val/
    dry_waste/
    e_waste/
    wet_waste/
  test/
    dry_waste/
    e_waste/
    wet_waste/
```

Training requires at least one image in each `train` and `val` class. Keep the test split separate until final evaluation. Use representative, correctly labelled images and avoid near-duplicate leakage between splits.

## API and portal

- Portal: `https://<render-service>/portal/`
- API docs: `https://<render-service>/docs`
- Health: `https://<render-service>/health`
- Readiness: `https://<render-service>/ready`

The API uses `X-API-Key`. Configure unique keys for contributor, trainer, admin and device roles. The browser portal accepts a user-supplied scoped key in memory; never paste privileged admin or device keys into a shared browser.

## Local development

Copy `.env.example` to `.env`, replace placeholders, then run:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

For local development without Supabase Storage credentials, the storage adapter falls back to `STORAGE_ROOT`. Install development dependencies with `pip install -e ".[server,edge,dev]"`.

## Edge client

Install the edge extra on the Pi, set `SORTEX_API_URL` and a device-scoped `SORTEX_DEVICE_API_KEY`, then run:

```bash
sortex-edge sync
sortex-edge predict path/to/image.jpg
```

After synchronization, prediction runs locally and does not require internet access.

## Development checks

```bash
ruff check .
pytest
```

## Safety and limitations

- The initial API-key scheme is an MVP trusted-team model, not full public identity management. Before inviting external contributors, add per-user sign-in, key rotation/revocation, rate limiting, audit logs and a browser-safe session flow.
- The free API and free queue are for prototypes, not production availability or durable job processing.
- The starter worker is suitable only for small CPU experiments. Larger datasets and repeated training need more RAM/CPU and may incur additional costs.
- No dataset or trained model is bundled. Do not claim accuracy before representative held-out testing.
- No camera protocol, GPIO, motor control or physical actuation is implemented. Keep any future machine actuation separate and independently safeguarded.
- Model confidence is not a calibrated probability or a safety guarantee.
