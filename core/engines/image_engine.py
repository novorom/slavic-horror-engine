from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
        
        # Generate final question slide with monster face and name
        final_output = self.image_dir / f"scene_{len(story.scenes) + 1:02}.jpg"
        final_prompt = (
            f"Close-up portrait of {story.monster} from slavic folklore, "
            f"terrifying face, eye contact, intense stare, "
            f"photorealistic horror, cinematic lighting, "
            f"dark atmosphere, vertical composition, no text"
        )
        self.logger.info("Generating final question slide with monster portrait")
        self.provider.generate_image(final_prompt, final_output)
        if not verify_image(final_output, self.config.video.size):
            self.logger.warning("Final question slide had wrong size after generation: %s", final_output)
        
        # Add monster name text to final slide
        try:
            img = Image.open(final_output)
            draw = ImageDraw.Draw(img)
            
            # Try to use a bold font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                except:
                    font = ImageFont.load_default()
            
            # Calculate text position (top center)
            text = story.monster.upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            width, height = img.size
            x = (width - text_width) // 2
            y = 50  # 50px from top
            
            # Add text shadow
            draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 255))
            # Add main text (white with red glow effect)
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
            
            img.save(final_output)
            self.logger.info("Added monster name to final question slide")
        except Exception as e:
            self.logger.warning("Failed to add monster name to final slide: %s", e)
        
        paths.append(final_output)
        
        return paths

    def generate_thumbnail(self, story: Story) -> Path:
        output = self.config.paths.output / "thumbnail.jpg"
        prompt = (
            f"Terrifying close-up of {story.monster}, eye contact, most frightening moment, "
            "photorealistic horror thumbnail, vertical composition, no text"
        )
        self.provider.generate_image(prompt, output)
        return output
