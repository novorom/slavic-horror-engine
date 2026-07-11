from __future__ import annotations

import hashlib
import logging
import random
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from core.config import ProjectConfig
from core.prompts.story import IMAGE_STYLE_SUFFIX
from core.providers.base import ImageProvider
from core.utils.image import cover_resize


class PollinationsImageProvider(ImageProvider):
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def generate_image(self, prompt: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = f"{prompt}, {IMAGE_STYLE_SUFFIX}"
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        url = self._build_url(prompt)
        last_error: Exception | None = None
        for attempt in range(1, self.config.pollinations.max_retries + 1):
            try:
                response = requests.get(url, timeout=self.config.pollinations.timeout_seconds)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
                image = cover_resize(image, self.config.video.size)
                image.save(output_path, quality=95, optimize=True)
                return output_path
            except Exception as exc:
                last_error = exc
                self.logger.warning("Pollinations attempt %s failed: %s", attempt, exc)
                time.sleep(1.5 * attempt)

        self.logger.error("Image generation failed, creating fallback frame: %s", last_error)
        self._fallback_image(prompt, output_path)
        return output_path

    def _build_url(self, prompt: str) -> str:
        seed = random.randint(1, 999_999_999)
        settings = self.config.pollinations
        return (
            f"{settings.base_url}/{quote(prompt)}"
            f"?width={settings.width}"
            f"&height={settings.height}"
            f"&model={settings.model}"
            f"&enhance={str(settings.enhance).lower()}"
            f"&safe={str(settings.safe).lower()}"
            f"&nologo={str(settings.nologo).lower()}"
            f"&seed={seed}"
        )

    def _fallback_image(self, prompt: str, output_path: Path) -> None:
        width, height = self.config.video.size
        digest = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        base = Image.new("RGB", (width, height), (9, 10, 12))
        draw = ImageDraw.Draw(base)
        for y in range(height):
            shade = int(18 + 38 * (y / height))
            draw.line((0, y, width, y), fill=(shade // 2, shade, shade + 8))
        random.seed(digest)
        for _ in range(120):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(2, 18)
            color = (random.randint(30, 80), random.randint(35, 85), random.randint(45, 95))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        base = base.filter(ImageFilter.GaussianBlur(1.2))
        vignette = Image.new("L", (width, height), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse((-width // 2, height // 8, width + width // 2, height), fill=190)
        vignette = vignette.filter(ImageFilter.GaussianBlur(220))
        base = Image.composite(base, ImageOps.colorize(vignette, black=(0, 0, 0), white=(28, 34, 40)), vignette)
        base.save(output_path, quality=95)
