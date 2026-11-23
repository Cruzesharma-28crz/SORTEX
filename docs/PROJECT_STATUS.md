# Project status

## Implemented in this repository

- Canonical three-class label definition.
- Custom CNN architecture initialized from scratch.
- Shared image transforms for training and inference.
- Train/validation loop with best-validation checkpoint saving.
- Checkpoint metadata and class-order validation.
- Single-image inference with an explicit confidence rejection threshold.
- Held-out folder evaluation with confusion matrix and per-class metrics.
- Dry-run-only routing simulation.
- CLI and automated tests.

## Not implemented

- Dataset collection portal or hosted dataset service.
- Dataset review, deduplication, and split-management application.
- ESP32 firmware, camera selection, and camera-to-Pi protocol.
- Raspberry Pi deployment benchmark.
- GPIO, motor drivers, sensors, encoders, pusher control, or physical actuation.
- Mechanical/electrical interlocks.

## Evidence required before claiming readiness

1. A versioned dataset with documented collection and split methodology.
2. Reproducible training runs and saved configuration.
3. A held-out test report, including per-class metrics and confusion matrix.
4. Performance measurements on the selected target hardware.
5. Separate mechanical and electrical safety review before hardware integration.
