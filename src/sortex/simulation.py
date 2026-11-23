"""Safe, non-actuating sorter decision simulation."""

from sortex.labels import validate_class


def route_prediction(label: str, confidence: float, threshold: float = 0.65) -> dict:
    if not 0.0 <= confidence <= 1.0 or not 0.0 <= threshold <= 1.0:
        raise ValueError("confidence and threshold must be between 0 and 1")
    if label == "unknown" or confidence < threshold:
        return {"status": "rejected", "destination": None, "reason": "low_confidence_or_unknown"}
    validate_class(label)
    return {"status": "simulated", "destination": label, "reason": "dry_run_only"}
