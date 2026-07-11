from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class SceneAssets(BaseModel):
    index: int
    text: str
    image_path: Path
    subtitle_image_path: Path
    audio_path: Path
    ambient_path: Path | None = None
    accent_path: Path | None = None
    whisper_path: Path | None = None
    stinger_path: Path | None = None
    duration: float


class RenderResult(BaseModel):
    video_path: Path
    thumbnail_path: Path
    story_path: Path
    metadata_path: Path
    youtube_path: Path
    instagram_path: Path
    tiktok_path: Path
    hashtags_path: Path
    subtitle_path: Path
    duration: float
    scene_count: int
