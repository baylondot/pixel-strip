from __future__ import annotations
from abc import ABC, abstractmethod
from PIL import Image

class RemovalBackend(ABC):
    name: str
    @abstractmethod
    def remove(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError

class IdentityBackend(RemovalBackend):
    name = "identity"
    def remove(self, image: Image.Image) -> Image.Image:
        return image.convert("RGBA")

class RemBGBackend(RemovalBackend):
    name = "rembg"
    def __init__(self, model: str = "u2net", gpu: bool = True) -> None:
        try:
            from rembg import new_session, remove
        except ImportError as exc:
            raise RuntimeError("rembg is not installed. Run: pip install -e '.[rembg]'") from exc
        providers: list[str] | None = None
        if gpu:
            try:
                import onnxruntime as ort
                available = set(ort.get_available_providers())
                if "CUDAExecutionProvider" in available:
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            except Exception:
                providers = None
        self._remove = remove
        try:
            self._session = new_session(model, providers=providers) if providers else new_session(model)
        except TypeError:
            self._session = new_session(model)

    def remove(self, image: Image.Image) -> Image.Image:
        return self._remove(image, session=self._session).convert("RGBA")

def load_backend(name: str, **kwargs: object) -> RemovalBackend:
    normalized = name.strip().lower()
    if normalized == "rembg":
        return RemBGBackend(**kwargs)
    if normalized == "identity":
        return IdentityBackend()
    raise ValueError(f"Unknown backend '{name}'. Available: rembg, identity")
