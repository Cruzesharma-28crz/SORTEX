# Chatbot integration contract

SORTEX exposes a versioned REST API that a chatbot tool, bot server or agent can call. The chatbot should call SORTEX from its trusted backend, not directly from browser code with an administrator credential.

## Suggested tool actions

- create_dataset(name): POST /v1/datasets, contributor credential.
- upload_image(dataset_id, label, split, image): POST /v1/datasets/{dataset_id}/images, contributor credential.
- start_training(dataset_id, epochs, batch_size): POST /v1/training, trainer credential.
- get_training_status(job_id): GET /v1/training/{job_id}, trainer credential.
- list_models(): GET /v1/models, trainer credential.
- approve_model(model_id): POST /v1/models/{model_id}/approve, administrator credential only.

All requests use the X-API-Key header. Store credentials in the chatbot's server-side secret manager and assign the least-privileged role needed. Never return the key to the model, expose it in prompts, or send it to the browser. The chatbot should ask for explicit confirmation before starting a costly training run or approving a model.

## Example training action

Request body for POST /v1/training:

    {"dataset_id": "DATASET_UUID", "epochs": 30, "batch_size": 32}

The API returns a job ID. Poll its status endpoint until completed or failed. A completed job creates a pending-review model; it is not published to Raspberry Pi until an administrator approves it.

## Model publication

The Raspberry Pi uses a separate device key to request GET /v1/devices/model and download the approved bundle. The chatbot must not use or receive this device credential.

## Important

This contract makes SORTEX usable as a chatbot tool backend. The repository does not include a hosted LLM provider integration or a bot-provider secret. Choose the chatbot platform/provider separately, then connect its server-side tools to these endpoints.
