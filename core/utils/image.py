from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def cover_resize(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    target_width, target_height = target_size
    target_ratio = target_width / target_height
    image_ratio = image.width / image.height

    # Use letterbox (add black bars) instead of crop to preserve proportions
    if image_ratio > target_ratio:
        # Image is wider than target - scale by height
        new_height = target_height
        new_width = int(target_height * image_ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Crop width if needed
        if new_width > target_width:
            left = (new_width - target_width) // 2
            image = image.crop((left, 0, left + target_width, target_height))
    else:
        # Image is taller than target - scale by width
        new_width = target_width
        new_height = int(target_width / image_ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Crop height if needed
        if new_height > target_height:
            top = (new_height - target_height) // 2
            image = image.crop((0, top, target_width, top + target_height))

    return image


def verify_image(path: Path, expected_size: tuple[int, int]) -> bool:
    try:
        with Image.open(path) as image:
            return image.size == expected_size
    except Exception:
        return False
