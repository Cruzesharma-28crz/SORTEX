"""Checkpoint serialization and compatibility checks."""

from pathlib import Path

import torch

from sortex import __version__
from sortex.labels import CLASSES
from sortex.vision.model import SortexCNN


def save_checkpoint(model: SortexCNN, path: str | Path, epoch: int, score: float) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "format_version": 1,
            "sortex_version": __version__,
            "classes": list(CLASSES),
            "image_size": 160,
            "epoch": epoch,
            "validation_accuracy": score,
            "model_state": model.state_dict(),
        },
        destination,
    )


def load_checkpoint(path: str | Path, device: torch.device):
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get("format_version") != 1 or tuple(payload.get("classes", ())) != CLASSES:
        raise ValueError("Unsupported checkpoint format or class ordering")
    model = SortexCNN(num_classes=len(CLASSES))
    model.load_state_dict(payload["model_state"])
    model.to(device)
    model.eval()
    return model, payload
