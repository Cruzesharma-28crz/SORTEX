import pytest

from sortex.labels import CLASSES, validate_class


def test_class_order_is_stable():
    assert CLASSES == ("e_waste", "dry_waste", "wet_waste")


@pytest.mark.parametrize("label", CLASSES)
def test_valid_class(label):
    assert validate_class(label) == label


def test_invalid_class_is_rejected():
    with pytest.raises(ValueError):
        validate_class("plastic")
