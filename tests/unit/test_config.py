import pytest
from pydantic import ValidationError
from pixelstrip.config import ProcessingConfig, RunConfig

def test_config_defaults_and_valid_dimensions():
    c = ProcessingConfig(width=100, height=100, padding=10)
    assert c.workers == 1 and c.output_format == "png"

def test_config_rejects_invalid_dimensions():
    with pytest.raises(ValidationError):
        ProcessingConfig(width=100)
    with pytest.raises(ValidationError):
        ProcessingConfig(width=10, height=10, padding=5)

def test_run_config_uses_independent_defaults(tmp_path):
    a = RunConfig(input_dir=tmp_path, output_dir=tmp_path / "a")
    b = RunConfig(input_dir=tmp_path, output_dir=tmp_path / "b")
    assert a.processing is not b.processing
