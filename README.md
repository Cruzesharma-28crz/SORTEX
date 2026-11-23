# SORTEX

**SORTEX** classifies waste images into three classes: `e_waste`, `dry_waste`, and `wet_waste`.

This is a research prototype built around a custom CNN trained on SORTEX-collected images. An ESP32-class camera is the planned image source and a Raspberry Pi is the planned inference computer. Camera transport and physical actuation are not finalized.

> **Status:** software foundation. No dataset, trained weights, camera firmware, or validated hardware controller is included. Predictions are not safety-critical decisions.

## Architecture

```text
Camera node (planned) -> image transport (TBD) -> SORTEX inference
                                                   |
                                                   v
                                        class + confidence
                                                   |
                                                   v
                                       coordinator (dry-run)
```

Training happens on a development computer. A trained checkpoint can later be benchmarked on the target Pi.

## Install

Python 3.10+ is recommended. Create a virtual environment, install a suitable PyTorch/Torchvision build for your platform, then install SORTEX:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Dataset layout

Keep train, validation, and test sets separate. The test set must not be used for training or model selection.

```text
data/waste/
  train/{e_waste,dry_waste,wet_waste}/
  val/{e_waste,dry_waste,wet_waste}/
  test/{e_waste,dry_waste,wet_waste}/
```

Use varied objects, backgrounds, lighting, orientations, and distances. Split by physical object or collection session where possible to reduce leakage. Do not include faces or personal information.

## Commands

```bash
sortex train --data data/waste --output artifacts/sortex-cnn.pt --epochs 30
sortex evaluate --data data/waste/test --checkpoint artifacts/sortex-cnn.pt
sortex predict path/to/image.jpg --checkpoint artifacts/sortex-cnn.pt
sortex simulate --class dry_waste --confidence 0.94
```

The custom CNN is in `src/sortex/vision/model.py`. Class order is centralized in `src/sortex/labels.py` and saved in checkpoints. Evaluation reports a confusion matrix and per-class precision, recall, and F1. Do not publish accuracy claims until a representative held-out test set has been evaluated.

## Development

```bash
pytest
ruff check .
ruff format --check .
```

## Roadmap

1. Collect and review a balanced dataset.
2. Train and evaluate the baseline CNN with reproducible settings.
3. Finalize a versioned camera transport contract after choosing the camera.
4. Benchmark inference on the exact Raspberry Pi model.
5. Validate mechanical and electrical safety independently before considering physical actuation.

## Safety boundaries

- The coordinator is simulation-only. There is no GPIO or motor-control implementation.
- Low-confidence/unknown predictions must be rejected for human review.
- Never connect actuators based solely on a model prediction.
- Keep moving mechanisms isolated during software development.
