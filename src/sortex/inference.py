"""Single-image inference with an explicit reject threshold."""

from pathlib import Path

import torch
from PIL import Image

from sortex.labels import CLASSES
from sortex.vision.checkpoint import load_checkpoint
from sortex.vision.transforms import inference_transform


def predict(image_path: str, checkpoint: str, threshold: float = 0.65) -> dict:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, metadata = load_checkpoint(checkpoint, device)
    image = Image.open(Path(image_path)).convert("RGB")
    tensor = inference_transform()(image).unsqueeze(0).to(device)
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0].cpu().tolist()
    best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
    confidence = probabilities[best_index]
    accepted = confidence >= threshold
    return {
        "label": CLASSES[best_index] if accepted else "unknown",
        "confidence": round(confidence, 5),
        "accepted": accepted,
        "probabilities": {name: round(probabilities[i], 5) for i, name in enumerate(CLASSES)},
        "checkpoint_version": metadata.get("sortex_version", "unknown"),
    }
