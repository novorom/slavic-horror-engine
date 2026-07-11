from PIL import Image

from core.utils.image import cover_resize


def test_cover_resize_keeps_target_size_without_distortion() -> None:
    image = Image.new("RGB", (2400, 1200), "red")

    result = cover_resize(image, (1080, 1920))

    assert result.size == (1080, 1920)
