from typer.testing import CliRunner
from PIL import Image
from pixelstrip.cli import app

def test_cli_identity(tmp_path):
    src, dst = tmp_path / "in", tmp_path / "out"
    src.mkdir()
    Image.new("RGB", (10, 10), "red").save(src / "x.png")
    result = CliRunner().invoke(app, ["run", "--input", str(src), "--output", str(dst), "--backend", "identity"])
    assert result.exit_code == 0, result.output
    assert (dst / "x.png").exists()

def test_cli_rejects_nested_output(tmp_path):
    src = tmp_path / "in"; src.mkdir()
    result = CliRunner().invoke(app, ["run", "--input", str(src), "--output", str(src / "out"), "--backend", "identity"])
    assert result.exit_code != 0

def test_cli_version():
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "1.0.0"

def test_cli_requires_matching_dimensions(tmp_path):
    src, dst = tmp_path / "in", tmp_path / "out"
    src.mkdir()
    result = CliRunner().invoke(app, ["run", "--input", str(src), "--output", str(dst), "--backend", "identity", "--width", "10"])
    assert result.exit_code != 0

def test_cli_rejects_bad_format(tmp_path):
    src, dst = tmp_path / "in", tmp_path / "out"
    src.mkdir()
    result = CliRunner().invoke(app, ["run", "--input", str(src), "--output", str(dst), "--backend", "identity", "--format", "jpg"])
    assert result.exit_code != 0
