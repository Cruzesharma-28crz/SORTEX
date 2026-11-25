# SORTEX Trainer integration contract

SORTEX exposes a versioned REST API that a team chatbot or trainer interface can call. The chatbot should call SORTEX from its trusted backend, not directly from browser code with an administrator credential.

## Team contribution workflow

1. A contributor creates or is assigned a dataset using `POST /v1/datasets`.
2. The contributor uploads a labelled image using `POST /v1/datasets/{dataset_id}/images`.
3. The API validates the class, file type, image contents and upload size, then stores the image and its label.
4. A trainer exports the dataset using `GET /v1/datasets/{dataset_id}/export`. The ZIP contains `train/`, `val/`, and `test/` folders with the three SORTEX class folders, plus `manifest.json`. It can be extracted into Google Drive and used by the Colab training notebook.
5. A trainer can request cloud training using `POST /v1/training` when the background worker is configured. A completed run creates a model pending review.
6. An administrator approves a reviewed model using `POST /v1/models/{model_id}/approve`.

## Dataset classes

The only accepted labels are:

- `dry_waste`
- `e_waste`
- `wet_waste`

Splits are `train`, `val`, and `test`. Contributors should not upload the same original photograph into multiple splits.

## API authentication

All protected requests use the `X-API-Key` header. The API supports separate `contributor`, `trainer`, `admin`, and `device` roles. Store credentials in the chatbot's server-side secret manager and assign the least-privileged role needed. Never return an API key to the language model, expose it in browser code, or include it in prompts.

Suggested actions for a team chatbot:

- `create_dataset(name)`: `POST /v1/datasets`, contributor key.
- `upload_image(dataset_id, label, split, image)`: `POST /v1/datasets/{dataset_id}/images`, contributor key.
- `list_datasets()`: `GET /v1/datasets`, trainer key.
- `export_dataset(dataset_id)`: `GET /v1/datasets/{dataset_id}/export`, trainer key.
- `start_training(dataset_id, epochs, batch_size)`: `POST /v1/training`, trainer key.
- `get_training_status(job_id)`: `GET /v1/training/{job_id}`, trainer key.
- `list_models()`: `GET /v1/models`, trainer key.
- `approve_model(model_id)`: `POST /v1/models/{model_id}/approve`, administrator key.

The chatbot must ask for explicit confirmation before starting a costly training run or approving a model.

## SORTEX 1.0 model release

The first model family is named **SORTEX 1.0**. Its first trained checkpoint is version `1.0.0`; subsequent training releases increment the patch version. New models remain pending review until an administrator approves them.

## Raspberry Pi model publication

The Raspberry Pi uses a separate device key to request `GET /v1/devices/model` and download the approved bundle. The chatbot must not use or receive this device credential.

## Deployment requirements

The API requires a PostgreSQL `DATABASE_URL`, Supabase `SUPABASE_URL` and server-only `SUPABASE_SERVICE_ROLE_KEY`, a configured `SORTEX_API_KEYS_JSON`, and Redis `REDIS_URL` if queued cloud training is enabled. Never commit these secrets to GitHub.

The API and dataset collection can be deployed separately from model training. The dataset export endpoint allows Colab to retrieve the collected images; the current Render worker is not a substitute for a suitably resourced training runtime.

## Chatbot provider

This repository defines the secure API contract, not a hosted LLM chatbot. A chatbot UI/provider still needs to be connected to these server-side actions. The bot should not claim a model has been trained until it checks the training result and model registry.
