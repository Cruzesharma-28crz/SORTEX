from pathlib import Path

import pytest

from sortex.data.layout import validate_dataset
from sortex.labels import CLASSES


def test_missing_dataset_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="Missing split"):
        validate_dataset(tmp_path, ("train",))


def test_empty_class_folder_is_rejected(tmp_path: Path):
    for split in ("train", "val"):
        for label in CLASSES:
            (tmp_path / split / label).mkdir(parents=True)
    with pytest.raises(ValueError, match="no images"):
        validate_dataset(tmp_path, ("train", "val"))
