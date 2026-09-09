from pathlib import Path
from PIL import Image
from pixelstrip.core.batch_runner import run_batch

def test_batch_creates_output_and_manifest(tmp_path: Path):
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir()
    Image.new("RGB", (16, 8), "white").save(src / "a.jpg")
    Image.new("RGB", (8, 8), "red").save(src / "nested.png")
    results = run_batch(src, dst, "identity", 2, 32, 32, 2, "png", 72, False)
    assert len(results) == 2
    assert all(r["status"] == "processed" for r in results)
    assert (dst / "a.png").exists() and (dst / "nested.png").exists()
    assert (dst / "manifest.json").exists() and (dst / ".pixelstrip-manifest.json").exists()

def test_existing_output_is_skipped(tmp_path: Path):
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir(); dst.mkdir()
    Image.new("RGB", (5, 5), "white").save(src / "a.png")
    Image.new("RGBA", (5, 5), (1,2,3,255)).save(dst / "a.png")
    results = run_batch(src, dst, "identity")
    assert results[0]["status"] == "skipped"


def test_cache_hit_on_second_run(tmp_path: Path):
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir()
    Image.new("RGB", (12, 12), "blue").save(src / "a.png")
    first = run_batch(src, dst, "identity", 1)
    second = run_batch(src, dst, "identity", 1)
    assert first[0]["status"] == "processed"
    assert second[0]["status"] == "skipped"
    assert second[0]["reason"] == "cache_hit"

def test_corrupt_file_isolated(tmp_path: Path):
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir()
    (src / "bad.png").write_bytes(b"not-an-image")
    Image.new("RGB", (4, 4), "green").save(src / "good.png")
    results = run_batch(src, dst, "identity", 1)
    assert [r["status"] for r in results] == ["failed", "processed"]

def test_webp_and_padding(tmp_path: Path):
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir()
    Image.new("RGB", (10, 5), "white").save(src / "a.jpg")
    results = run_batch(src, dst, "identity", 1, 20, 20, 2, "webp", 96)
    assert results[0]["status"] == "processed"
    with Image.open(dst / "a.webp") as image:
        assert image.size == (20, 20)

def test_hash_and_empty_batch(tmp_path: Path):
    from pixelstrip.core.batch_runner import content_hash
    src, dst = tmp_path / "raw", tmp_path / "clean"
    src.mkdir(); (src / "x.txt").write_text("x", encoding="utf-8")
    assert len(content_hash(src / "x.txt")) == 64
    assert run_batch(src, dst, "identity") == []

def test_process_one_invalid_image(tmp_path: Path):
    from pixelstrip.core.batch_runner import Job, _process
    src = tmp_path / "bad.png"; dst = tmp_path / "bad-out.png"
    src.write_bytes(b"broken")
    job = Job(str(src), str(dst), "identity", None, None, 0, "png", 72, False)
    result = _process(job)
    assert result["status"] == "failed"

def test_manifest_cache_loader_and_atomic_save(tmp_path: Path):
    from pixelstrip.core.batch_runner import _load_cache, _save
    from PIL import Image
    path = tmp_path / "manifest.json"
    assert _load_cache(path) == {}
    path.write_text("{bad", encoding="utf-8")
    assert _load_cache(path) == {}
    path.write_text('{"x": {"ok": true}}', encoding="utf-8")
    assert _load_cache(path)["x"]["ok"] is True
    out = tmp_path / "out.png"
    _save(Image.new("RGBA", (2, 2), "red"), out, "png", 72)
    assert out.exists()

def test_process_one_happy_path(tmp_path: Path):
    from pixelstrip.core.batch_runner import Job, _process
    src, dst = tmp_path / "a.png", tmp_path / "a-out.png"
    Image.new("RGB", (3, 4), "red").save(src)
    job = Job(str(src), str(dst), "identity", 8, 8, 1, "png", 72, True)
    result = _process(job)
    assert result["status"] == "processed" and dst.exists()
