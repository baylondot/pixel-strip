from __future__ import annotations
import hashlib
import json
import logging
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from PIL import Image, UnidentifiedImageError
from .normalizer import normalize
from .remover import load_backend

LOGGER = logging.getLogger("pixelstrip")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
_BACKEND = None

@dataclass(frozen=True)
class Job:
    source: str
    output: str
    backend: str
    width: int | None
    height: int | None
    padding: int
    fmt: str
    dpi: int
    overwrite: bool


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_path(output_dir: Path) -> Path:
    return output_dir / ".pixelstrip-manifest.json"


def _load_cache(path: Path) -> dict[str, dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save(image: Image.Image, dest: Path, fmt: str, dpi: int) -> None:
    """Write an output atomically so a failed job never leaves a partial target."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".webp" if fmt == "webp" else ".png"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.stem}.", suffix=suffix, dir=dest.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        kwargs = {"dpi": (dpi, dpi)}
        if fmt == "webp":
            image.save(tmp, format="WEBP", lossless=True, **kwargs)
        else:
            image.save(tmp, format="PNG", **kwargs)
        os.replace(tmp, dest)
    finally:
        if tmp.exists():
            tmp.unlink()


def _init_worker(backend: str) -> None:
    global _BACKEND
    _BACKEND = load_backend(backend)


def _process(job: Job) -> dict[str, object]:
    global _BACKEND
    src, dst = Path(job.source), Path(job.output)
    try:
        digest = content_hash(src)
        if dst.exists() and not job.overwrite:
            return {"status":"skipped", "source":str(src), "output":str(dst), "sha256":digest, "reason":"output_exists"}
        if _BACKEND is None:
            _BACKEND = load_backend(job.backend)
        with Image.open(src) as raw:
            raw.verify()
        with Image.open(src) as raw:
            raw.load()
            result = _BACKEND.remove(raw)
        result = normalize(result, job.width, job.height, job.padding)
        _save(result, dst, job.fmt, job.dpi)
        return {"status":"processed", "source":str(src), "output":str(dst), "sha256":digest}
    except (UnidentifiedImageError, OSError, ValueError, RuntimeError) as exc:
        LOGGER.exception("Failed processing %s", src)
        return {"status":"failed", "source":str(src), "output":str(dst), "error":str(exc)}
    except Exception as exc:
        LOGGER.exception("Unexpected failure processing %s", src)
        return {"status":"failed", "source":str(src), "output":str(dst), "error":f"unexpected: {exc}"}


def run_batch(input_dir: Path, output_dir: Path, backend: str = "rembg", workers: int = 1,
              width: int | None = None, height: int | None = None, padding: int = 0,
              fmt: str = "png", dpi: int = 72, overwrite: bool = False,
              on_result: Callable[[dict[str, object]], None] | None = None) -> list[dict[str, object]]:
    input_dir, output_dir = input_dir.resolve(), output_dir.resolve()
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if workers < 1: raise ValueError("workers must be >= 1")
    if fmt not in {"png", "webp"}: raise ValueError("format must be png or webp")
    if (width is None) != (height is None): raise ValueError("width and height must be supplied together")
    if padding < 0: raise ValueError("padding must be >= 0")
    if width is not None and padding * 2 >= min(width, height): raise ValueError("padding is too large")
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
    jobs = [Job(str(p), str(output_dir / p.relative_to(input_dir).with_suffix("." + fmt)), backend, width, height, padding, fmt, dpi, overwrite) for p in files]
    cache_path = _manifest_path(output_dir)
    old_cache = _load_cache(cache_path)
    results: list[dict[str, object]] = []
    pending: list[Job] = []
    for job in jobs:
        src = Path(job.source)
        dst = Path(job.output)
        digest = content_hash(src)
        cached = old_cache.get(str(src), {})
        same_config = (
            cached.get("sha256") == digest
            and cached.get("backend") == backend
            and cached.get("format") == fmt
            and cached.get("width") == width
            and cached.get("height") == height
            and cached.get("padding") == padding
            and cached.get("dpi") == dpi
        )
        if not overwrite and dst.exists() and same_config:
            result = {"status":"skipped", "source":str(src), "output":str(dst), "sha256":digest, "reason":"cache_hit"}
            results.append(result)
            if on_result: on_result(result)
        else:
            pending.append(job)
    if pending:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(backend,)) as pool:
            futures = [pool.submit(_process, job) for job in pending]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if on_result: on_result(result)
    results.sort(key=lambda r: str(r.get("source", "")))
    manifest: dict[str, dict[str, object]] = {}
    for result in results:
        if result["status"] in {"processed", "skipped"}:
            manifest[str(result["source"])] = {"sha256": result.get("sha256"), "output": result.get("output"), "status": result.get("status"), "backend": backend, "format": fmt, "width": width, "height": height, "padding": padding, "dpi": dpi}
        else:
            manifest[str(result["source"])] = {"status":"failed", "error":result.get("error")}
    # Preserve no stale cache entries: the manifest is authoritative for the current run.
    cache_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
