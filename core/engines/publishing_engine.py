from __future__ import annotations

import json
import logging
from pathlib import Path

from core.config import ProjectConfig
from core.models.assets import RenderResult
from core.models.story import Story


class PublishingEngine:
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def write_story(self, story: Story) -> Path:
        path = self.config.paths.output / "story.json"
        path.write_text(
            json.dumps(story.as_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def write_social_files(self, story: Story) -> dict[str, Path]:
        social = story.social
        files = {
            "youtube": self.config.paths.output / "youtube.txt",
            "instagram": self.config.paths.output / "instagram.txt",
            "tiktok": self.config.paths.output / "tiktok.txt",
            "hashtags": self.config.paths.output / "hashtags.txt",
        }
        files["youtube"].write_text(
            f"{social.youtube_title}\n\n{social.youtube_description}\n\n{' '.join(social.hashtags)}\n",
            encoding="utf-8",
        )
        files["instagram"].write_text(
            f"{social.instagram_caption}\n\n{' '.join(social.hashtags)}\n",
            encoding="utf-8",
        )
        files["tiktok"].write_text(
            f"{social.tiktok_caption}\n\n{' '.join(social.hashtags[:8])}\n",
            encoding="utf-8",
        )
        files["hashtags"].write_text(" ".join(social.hashtags) + "\n", encoding="utf-8")
        return files

    def write_metadata(self, story: Story, result: RenderResult) -> Path:
        path = self.config.paths.output / "metadata.json"
        payload = {
            "project": self.config.project.name,
            "title": story.title,
            "monster": story.monster,
            "language": self.config.project.language,
            "video": str(result.video_path),
            "thumbnail": str(result.thumbnail_path),
            "subtitle": str(result.subtitle_path),
            "duration": round(result.duration, 2),
            "scene_count": result.scene_count,
            "size": {"width": self.config.video.width, "height": self.config.video.height},
            "providers": self.config.providers.model_dump(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
