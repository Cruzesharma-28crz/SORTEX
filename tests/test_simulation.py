import pytest

from sortex.simulation import route_prediction


def test_confident_prediction_is_simulated_only():
    result = route_prediction("dry_waste", 0.9)
    assert result == {
        "status": "simulated",
        "destination": "dry_waste",
        "reason": "dry_run_only",
    }


def test_low_confidence_is_rejected():
    assert route_prediction("wet_waste", 0.4)["status"] == "rejected"


def test_unknown_is_rejected():
    assert route_prediction("unknown", 0.99)["destination"] is None


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError):
        route_prediction("dry_waste", 1.2)
