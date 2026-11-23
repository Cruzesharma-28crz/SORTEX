"""Shared image preprocessing."""

from torchvision.transforms import (
    ColorJitter,
    Compose,
    Normalize,
    RandomHorizontalFlip,
    RandomRotation,
    Resize,
    ToTensor,
)

IMAGE_SIZE = 160
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def training_transform():
    return Compose(
        [
            Resize((IMAGE_SIZE, IMAGE_SIZE)),
            RandomHorizontalFlip(),
            RandomRotation(10),
            ColorJitter(brightness=0.15, contrast=0.15, saturation=0.12),
            ToTensor(),
            Normalize(MEAN, STD),
        ]
    )


def inference_transform():
    return Compose(
        [
            Resize((IMAGE_SIZE, IMAGE_SIZE)),
            ToTensor(),
            Normalize(MEAN, STD),
        ]
    )
