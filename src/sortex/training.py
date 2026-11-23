"""Training loop for the custom SORTEX CNN."""

from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from sortex.data.layout import validate_dataset
from sortex.labels import CLASSES
from sortex.vision.checkpoint import save_checkpoint
from sortex.vision.model import SortexCNN
from sortex.vision.transforms import inference_transform, training_transform


def _run_epoch(model, loader, loss_fn, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = loss_fn(logits, labels)
            if training:
                loss.backward()
                optimizer.step()
        total_loss += loss.item() * labels.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += labels.size(0)
    return total_loss / total, correct / total


def train(data: str, output: str, epochs: int = 30, batch_size: int = 32) -> None:
    if epochs < 1 or batch_size < 1:
        raise ValueError("epochs and batch_size must be positive")
    root = Path(data)
    validate_dataset(root, ("train", "val"))
    train_set = ImageFolder(root / "train", transform=training_transform())
    val_set = ImageFolder(root / "val", transform=inference_transform())
    if tuple(train_set.classes) != CLASSES or train_set.classes != val_set.classes:
        raise ValueError(f"Dataset class order must be {list(CLASSES)}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)
    model = SortexCNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    loss_fn = nn.CrossEntropyLoss()
    best_score = -1.0
    for epoch in range(1, epochs + 1):
        train_loss, train_acc = _run_epoch(model, train_loader, loss_fn, device, optimizer)
        val_loss, val_acc = _run_epoch(model, val_loader, loss_fn, device)
        print(
            f"epoch={epoch:03d}/{epochs} train_loss={train_loss:.4f} "
            f"train_acc={train_acc:.3f} val_loss={val_loss:.4f} val_acc={val_acc:.3f}"
        )
        if val_acc > best_score:
            best_score = val_acc
            save_checkpoint(model, output, epoch, val_acc)
    print(f"Best validation accuracy: {best_score:.3f}; checkpoint: {output}")
