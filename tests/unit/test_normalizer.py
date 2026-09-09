from PIL import Image
from pixelstrip.core.normalizer import normalize

def test_normalize_preserves_aspect_ratio():
    img = Image.new("RGBA", (200, 100), "white")
    out = normalize(img, 100, 100, 10)
    assert out.size == (100, 100)
    assert out.getbbox() == (10, 30, 90, 70)

def test_padding_only():
    out = normalize(Image.new("RGBA", (10, 10), "white"), None, None, 5)
    assert out.size == (20, 20)

def test_normalize_rejects_mismatched_dimensions():
    import pytest
    with pytest.raises(ValueError):
        normalize(Image.new("RGBA", (5, 5)), 10, None, 0)

def test_normalize_rejects_excessive_padding():
    import pytest
    with pytest.raises(ValueError):
        normalize(Image.new("RGBA", (5, 5)), 10, 10, 5)
