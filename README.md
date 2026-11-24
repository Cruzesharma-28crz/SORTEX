# SORTEX

SORTEX is a hybrid cloud-edge waste-classification research platform. The cloud collects and manages datasets, trains and evaluates the custom CNN, and publishes approved model bundles. A Raspberry Pi downloads approved bundles and performs local inference offline.

**Current status:** software foundation and API/worker/edge implementation. No dataset, trained weights, cloud credentials, camera transport or validated hardware controller is included. Model outputs are not safety-critical decisions.

## Architecture

- Cloud API: FastAPI, role-scoped API keys, dataset intake, training orchestration and model registry.
- Data services: PostgreSQL metadata, persistent artifact storage, Redis/Celery training queue.
- Training worker: reuses the custom PyTorch CNN and optionally evaluates a held-out test split.
- Edge client: downloads approved model bundles, verifies SHA-256 and runs local inference.

See docs/HYBRID_ARCHITECTURE.md for the full lifecycle and deployment notes.

## Install the existing CLI

Python 3.10+ is required. Install a suitable PyTorch/Torchvision build for your platform, then:

    python -m venv .venv
    # Windows: .venv\\Scripts\\activate
    # Linux/macOS: source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -e ".[dev]"

## Run the cloud stack

Copy .env.example to .env and replace every placeholder with unique secrets. Then run:

    docker compose -f deploy/docker-compose.yml up --build

Browser control panel: http://localhost:8000/portal/ · API docs: http://localhost:8000/docs · health: http://localhost:8000/health.

Install server and edge extras for local development:

    pip install -e ".[server,edge,dev]"

The API uses X-API-Key. Configure separate contributor, trainer, admin and device keys in SORTEX_API_KEYS_JSON. Never put privileged keys in browser code or commit a real .env file.

## Edge client

Set SORTEX_API_URL and SORTEX_DEVICE_API_KEY on the Pi, then:

    sortex-edge sync
    sortex-edge predict path/to/image.jpg

After synchronization, prediction runs locally and does not require internet access.

## Existing model commands

    sortex train --data data/waste --output artifacts/sortex-cnn.pt --epochs 30
    sortex evaluate --data data/waste/test --checkpoint artifacts/sortex-cnn.pt
    sortex predict path/to/image.jpg --checkpoint artifacts/sortex-cnn.pt
    sortex simulate --class dry_waste --confidence 0.94

## Development checks

    ruff check .
    ruff format --check .
    pytest

## Safety and limitations

- Cloud artifact storage is a persistent filesystem volume in this first implementation. Back it up; multi-host deployments need shared object storage.
- API keys provide an initial trusted-team access model, not full user identity management. Add per-user auth, revocation, rate limiting and audit logs before public use.
- Training needs a suitable cloud CPU/RAM machine; the worker is isolated from the API.
- No dataset or trained model is bundled. Do not claim accuracy before representative held-out testing.
- No camera protocol, GPIO, motor control or physical actuation is implemented. Keep actuation separate and independently safeguarded.
