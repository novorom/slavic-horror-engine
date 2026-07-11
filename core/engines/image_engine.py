from __future__ import annotations

import logging
from pathlib import Path

from core.config import ProjectConfig
from core.models.story import Story
from core.providers.base import ImageProvider
from core.utils.image import verify_image


class ImageEngine:
    def __init__(self, config: ProjectConfig, provider: ImageProvider, logger: logging.Logger):
        self.config = config
        self.provider = provider
        self.logger = logger
        self.image_dir = config.paths.cache / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def generate_scene_images(self, story: Story) -> list[Path]:
        paths: list[Path] = []
        for scene in story.scenes:
            output = self.image_dir / f"scene_{scene.index:02}.jpg"
            self.logger.info("Generating image %s/%s", scene.index, len(story.scenes))
            path = self.provider.generate_image(scene.image_prompt, output)
            if not verify_image(path, self.config.video.size):
                self.logger.warning("Image had wrong size after generation: %s", path)
            paths.append(path)
        return paths

    def generate_thumbnail(self, story: Story) -> Path:
        output = self.config.paths.output / "thumbnail.jpg"
        prompt = (
            f"Terrifying close-up of {story.monster}, eye contact, most frightening moment, "
            "photorealistic horror thumbnail, vertical composition, no text"
        )
        self.provider.generate_image(prompt, output)
        return output
