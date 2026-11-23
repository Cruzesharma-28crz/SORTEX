"""Validate the expected ImageFolder dataset layout."""

from pathlib import Path

from sortex.labels import CLASSES

SPLITS = ("train", "val", "test")


def validate_dataset(root: str | Path, required_splits: tuple[str, ...] = SPLITS) -> None:
    root = Path(root)
    errors = []
    for split in required_splits:
        split_dir = root / split
        if not split_dir.is_dir():
            errors.append(f"Missing split directory: {split_dir}")
            continue
        found = {p.name for p in split_dir.iterdir() if p.is_dir()}
        missing = set(CLASSES) - found
        extra = found - set(CLASSES)
        if missing:
            errors.append(f"{split}: missing class folders {sorted(missing)}")
        if extra:
            errors.append(f"{split}: unexpected class folders {sorted(extra)}")
        for label in CLASSES:
            folder = split_dir / label
            if folder.is_dir() and not any(p.is_file() for p in folder.iterdir()):
                errors.append(f"{split}/{label}: no images found")
    if errors:
        raise ValueError("Invalid dataset:\n- " + "\n- ".join(errors))
