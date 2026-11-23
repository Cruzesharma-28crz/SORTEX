"""Held-out test-set evaluation."""

from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from sortex.data.layout import validate_dataset
from sortex.labels import CLASSES
from sortex.vision.checkpoint import load_checkpoint
from sortex.vision.transforms import inference_transform


def evaluate(data: str, checkpoint: str) -> dict:
    root = Path(data)
    if root.name == "test":
        validate_dataset(root.parent, ("test",))
    dataset = ImageFolder(root, transform=inference_transform())
    if tuple(dataset.classes) != CLASSES:
        raise ValueError(f"Test class order must be {list(CLASSES)}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = load_checkpoint(checkpoint, device)
    loader = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)
    matrix = [[0 for _ in CLASSES] for _ in CLASSES]
    with torch.inference_mode():
        for images, labels in loader:
            predictions = model(images.to(device)).argmax(1).cpu()
            for actual, predicted in zip(labels.tolist(), predictions.tolist(), strict=True):
                matrix[actual][predicted] += 1

    metrics = {}
    total = sum(map(sum, matrix))
    correct = sum(matrix[i][i] for i in range(len(CLASSES)))
    for index, label in enumerate(CLASSES):
        true_positive = matrix[index][index]
        false_positive = sum(matrix[row][index] for row in range(len(CLASSES))) - true_positive
        false_negative = sum(matrix[index]) - true_positive
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(matrix[index]),
        }

    return {
        "accuracy": correct / total if total else 0.0,
        "samples": total,
        "classes": metrics,
        "confusion_matrix": matrix,
    }
