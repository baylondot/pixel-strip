# pixel-strip

Production-oriented batch background removal and image normalization for computer-vision/ML asset preparation.

## What it does

- Recursively discovers common raster image formats.
- Removes backgrounds through a pluggable backend (`rembg`/U²-Net by default).
- Preserves alpha and normalizes images to an exact canvas without distortion.
- Supports configurable transparent padding and PNG/WebP output; PNG preserves configured DPI metadata.
- Processes batches concurrently with isolated worker processes.
- Continues after individual file failures and returns a non-zero CLI exit code if any failed.
- Writes a machine-readable `manifest.json` plus an internal content-hash manifest.
- Skips existing outputs unless `--overwrite` is supplied.
- Uses CUDA automatically when a CUDA-enabled ONNX Runtime provider is available; otherwise CPU is used.

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,rembg]"
```

For NVIDIA GPU inference, install the GPU extra instead of the CPU ONNX Runtime package:

```bash
pip uninstall -y onnxruntime
pip install -e ".[dev,rembg,gpu]"
```

## Run

```bash
pixelstrip run --input ./raw_images --output ./clean --workers 4 --backend rembg
```

Exact normalization:

```bash
pixelstrip run --input ./raw_images --output ./clean --workers 4 --width 1024 --height 1024 --padding 64 --format webp --dpi 144
```

Dry, dependency-free pipeline test:

```bash
pixelstrip run --input ./raw_images --output ./clean --backend identity
```

The identity backend performs no background removal; it is intended for deterministic tests and pipeline validation.

## Output

The relative input directory structure is preserved. A run produces:

- processed images
- `manifest.json`: per-file run results
- `.pixelstrip-manifest.json`: compact content/output state

## Development checks

```bash
ruff check .
mypy src
pytest
```

The test suite enforces an 85% coverage floor.

## Architecture

`CLI → validation/config → recursive discovery → worker pool → backend → normalization → atomic output → manifests`

The backend boundary is deliberately isolated so model implementations can be replaced without changing the batch orchestration layer.

## Scaling path

The local process pool is the single-node execution layer. The same job model can be moved behind a durable queue (Redis/Celery or another worker system) without changing the image transformation contract. Container and CI definitions are included for repeatable deployment.

## Security and reliability

Only process assets you are authorized to handle. Input files are never executed. Corrupt/unreadable images are isolated as failed jobs rather than terminating the entire batch.

## License

MIT
