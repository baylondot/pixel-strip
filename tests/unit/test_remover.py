import sys
import types
import pytest
from PIL import Image
from pixelstrip.core.remover import IdentityBackend, load_backend, RemBGBackend

def test_identity_backend_returns_rgba():
    out = IdentityBackend().remove(Image.new("RGB", (2, 2), "red"))
    assert out.mode == "RGBA"

def test_unknown_backend_rejected():
    with pytest.raises(ValueError, match="Unknown backend"):
        load_backend("nope")

def test_rembg_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "rembg", types.ModuleType("rembg"))
    with pytest.raises(RuntimeError, match="rembg is not installed"):
        RemBGBackend()

def test_rembg_backend_with_fake_module(monkeypatch):
    mod = types.ModuleType("rembg")
    class Session: pass
    mod.new_session = lambda model, providers=None: Session()
    mod.remove = lambda image, session=None: image.convert("RGBA")
    monkeypatch.setitem(sys.modules, "rembg", mod)
    backend = RemBGBackend(gpu=False)
    assert backend.remove(Image.new("RGB", (2, 2))).mode == "RGBA"

def test_load_backend_case_insensitive():
    assert load_backend(" IDENTITY ").name == "identity"

def test_abstract_backend_cannot_be_instantiated():
    from pixelstrip.core.remover import RemovalBackend
    with pytest.raises(TypeError):
        RemovalBackend()

def test_rembg_cuda_provider(monkeypatch):
    mod = types.ModuleType("rembg")
    calls = {}
    class Session: pass
    def new_session(model, providers=None):
        calls["providers"] = providers
        return Session()
    mod.new_session = new_session
    mod.remove = lambda image, session=None: image
    ort = types.ModuleType("onnxruntime")
    ort.get_available_providers = lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"]
    monkeypatch.setitem(sys.modules, "rembg", mod)
    monkeypatch.setitem(sys.modules, "onnxruntime", ort)
    RemBGBackend(gpu=True)
    assert calls["providers"] == ["CUDAExecutionProvider", "CPUExecutionProvider"]

def test_rembg_typeerror_fallback(monkeypatch):
    mod = types.ModuleType("rembg")
    calls = {"n": 0}
    def new_session(model, providers=None):
        calls["n"] += 1
        if providers is not None:
            raise TypeError("providers unsupported")
        return object()
    mod.new_session = new_session
    mod.remove = lambda image, session=None: image
    monkeypatch.setitem(sys.modules, "rembg", mod)
    RemBGBackend(gpu=False)
    assert calls["n"] == 1
