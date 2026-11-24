# SORTEX Hybrid Cloud-Edge Architecture

## Operating model

- Cloud handles dataset intake, metadata, training jobs, evaluation, model review and version distribution.
- Raspberry Pi downloads approved model bundles and performs inference locally.
- Internet is required for uploads, training and synchronization, not ordinary local inference.

## Services

| Service | Responsibility |
| --- | --- |
| FastAPI | Authenticated control-plane API |
| PostgreSQL | Dataset, image, job and model metadata |
| Persistent volume | Original images and model bundles |
| Redis + Celery | Asynchronous training queue |
| Training worker | Existing PyTorch CNN and optional test evaluation |
| Edge client | Verifies and installs approved bundles, then predicts offline |

## Roles and credentials

API keys are configured server-side in SORTEX_API_KEYS_JSON. Roles are contributor, trainer, admin and device. Never place privileged keys in browser code. This is an MVP trusted-team credential scheme; before inviting external users, add individual sign-in, key rotation/revocation, rate limits, audit logs and a browser-safe session flow.

## Dataset and training

Each dataset is stored at STORAGE_ROOT/datasets/<dataset-id>/{train,val,test}/<class>/. Uploads are size-limited and validated as images. Contributors own datasets. Training requires train and validation images; test data is reserved for final reporting. Celery runs training separately from the API process.

## Model lifecycle

1. Trainer creates a job; Celery queues it.
2. Worker trains the custom CNN.
3. If a test split exists, worker evaluates it.
4. Worker packages weights, preprocessing metadata and labels into a ZIP and records SHA-256.
5. Model remains pending_review.
6. Admin approves it; previous approved version is retired.
7. Pi polls the manifest, downloads the bundle and verifies SHA-256 before installation.

## Local deployment

1. Copy .env.example to .env and replace all placeholders with unique random secrets.
2. Run docker compose -f deploy/docker-compose.yml up --build.
3. API docs: http://localhost:8000/docs; health: http://localhost:8000/health.
4. Install edge package on Pi with pip install -e '.[edge]'; set SORTEX_API_URL and SORTEX_DEVICE_API_KEY.
5. Run sortex-edge sync, then sortex-edge predict path/to/image.jpg offline.

Use X-API-Key for API requests. Create a dataset with POST /v1/datasets, upload images to POST /v1/datasets/{id}/images?label=dry_waste&split=train, then start training with POST /v1/training.

## Limitations

- Artifacts use a persistent filesystem volume. Back it up; multi-host scaling requires shared object storage.
- API keys are not full user identity management.
- No dataset, trained weights, camera transport, Pi hardware configuration or actuator integration is included.
- Confidence is not a calibrated probability or safety guarantee. Reject low-confidence results and use independent physical safeguards.
- Cloud training requires a suitable CPU/RAM machine, optionally a compatible GPU. Worker is separate from API.
