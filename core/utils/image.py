from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def cover_resize(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    target_width, target_height = target_size
    target_ratio = target_width / target_height
    image_ratio = image.width / image.height

    # Allow small tolerance for aspect ratio differences
    tolerance = 0.05
    
    if abs(image_ratio - target_ratio) < tolerance:
        # Close enough, just resize
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    if image_ratio > target_ratio:
        new_width = int(image.height * target_ratio)
        left = max((image.width - new_width) // 2, 0)
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = int(image.width / target_ratio)
        top = max((image.height - new_height) // 2, 0)
        image = image.crop((0, top, image.width, top + new_height))

    return image.resize(target_size, Image.Resampling.LANCZOS)


def verify_image(path: Path, expected_size: tuple[int, int]) -> bool:
    try:
        with Image.open(path) as image:
            return image.size == expected_size
    except Exception:
        return False
