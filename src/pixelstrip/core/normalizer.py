from __future__ import annotations
from PIL import Image, ImageOps

def normalize(image: Image.Image, width: int | None, height: int | None, padding: int = 0) -> Image.Image:
    """Convert to RGBA and optionally fit inside an exact canvas while preserving aspect ratio."""
    image = image.convert("RGBA")
    if width is None and height is None:
        return ImageOps.expand(image, border=padding, fill=(0, 0, 0, 0)) if padding else image
    if width is None or height is None:
        raise ValueError("width and height must be provided together")
    if padding * 2 >= min(width, height):
        raise ValueError("padding must leave at least one pixel of inner area")
    target = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    inner = (width - 2 * padding, height - 2 * padding)
    fitted = ImageOps.contain(image, inner, method=Image.Resampling.LANCZOS)
    x = (width - fitted.width) // 2
    y = (height - fitted.height) // 2
    target.alpha_composite(fitted, (x, y))
    return target
