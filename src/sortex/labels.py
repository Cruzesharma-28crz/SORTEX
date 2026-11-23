"""Canonical class labels and validation."""

# Alphabetical order matches torchvision ImageFolder's deterministic class indexing.
CLASSES = ("dry_waste", "e_waste", "wet_waste")


def validate_class(label: str) -> str:
    """Return a valid class label or raise ValueError."""
    if label not in CLASSES:
        raise ValueError(f"Unknown class {label!r}; expected one of {CLASSES}")
    return label
