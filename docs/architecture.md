# Architecture

## Pipeline

```text
CLI
 │
 ▼
Validate options
 │
 ▼
Recursive discovery ──► supported raster files
 │
 ▼
ProcessPoolExecutor
 │
 ├── load backend once per worker
 ├── hash source
 ├── validate/decode image
 ├── background removal
 ├── RGBA normalization
 └── PNG/WebP write
 │
 ▼
Run manifest + content-hash manifest
```

## Design decisions

### Backend isolation
`RemovalBackend` is the stable interface. `RemBGBackend` owns model/session initialization. Workers initialize their own backend so model state is not shared unsafely across processes.

### Concurrency
CPU-bound image work runs in separate processes. Model inference remains inside each worker. This avoids relying on Python threads for CPU parallelism and prevents one process from mutating another worker's model state.

### Idempotency
Every source gets a SHA-256 content hash. Existing outputs are skipped by default. The hash is persisted in the run manifest so external systems can audit which source content produced an output.

### Failure isolation
Each job catches expected image/runtime failures and returns a structured `failed` result. The batch completes all independent jobs. The CLI exits with code 1 when at least one job failed.

### GPU fallback
When ONNX Runtime reports `CUDAExecutionProvider`, the rembg session is initialized with CUDA first and CPU second. If CUDA is unavailable, the backend uses the default CPU-capable session.

## Future distributed deployment

The `Job` contract is serializable. A queue worker can consume the same job fields and invoke `_process` without changing normalization or backend semantics. A durable queue, object storage and distributed metrics can therefore be introduced at the infrastructure layer rather than mixed into image-processing code.
