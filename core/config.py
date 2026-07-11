from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathSettings(BaseModel):
    assets: Path = Path("assets")
    cache: Path = Path("cache")
    output: Path = Path("output")
    logs: Path = Path("logs")
    music: Path = Path("assets/music")
    fonts: Path = Path("assets/fonts")


class ProviderSettings(BaseModel):
    story: str = "gemini"
    image: str = "pollinations"
    tts: str = "edge"


class GeminiSettings(BaseModel):
    model: str = "gemini-2.5-flash"
    api_key_envs: list[str] = Field(
        default_factory=lambda: [
            "GEMINI_API_KEYS",
            "GEMINI_API_KEY_1",
            "GEMINI_API_KEY_2",
            "GEMINI_API_KEY_3",
            "GEMINI_API_KEY",
        ]
    )
    temperature: float = 0.9
    max_retries: int = 3


class PollinationsSettings(BaseModel):
    base_url: str = "https://image.pollinations.ai/prompt"
    model: str = "flux"
    width: int = 1216
    height: int = 2160
    enhance: bool = True
    safe: bool = False
    nologo: bool = True
    timeout_seconds: int = 180
    max_retries: int = 3


class VideoSettings(BaseModel):
    width: int = 1080
    height: int = 1920
    fps: int = 30
    horizontal_stretch: float = 1.035
    codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"
    crf: int = 20
    scene_duration_seconds: float = 5.8
    fallback_duration_seconds: float = 5.0
    min_total_seconds: int = 35
    max_total_seconds: int = 62

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)


class StorySettings(BaseModel):
    scene_count: int = 8
    min_words_per_scene: int = 5
    max_words_per_scene: int = 12
    monsters: list[str] = Field(default_factory=lambda: ["Leshy", "Baba Yaga", "Rusalka"])


class AudioSettings(BaseModel):
    voice: str = "es-ES-AlvaroNeural"
    rate: str = "0%"
    pitch: str = "0Hz"
    volume: str = "+0%"
    macos_voice: str = "Grandma (Испанский (Испания))"
    voice_profile: str = "natural"
    voice_lowpass_hz: int = 4200
    voice_highpass_hz: int = 60
    music_volume: float = 0.12
    voice_ducking_floor: float = 0.08
    voice_ducking_rise: float = 0.75
    accent_volume: float = 0.28
    accent_tail_seconds: float = 2.0
    whisper_volume: float = 0.18
    whisper_tail_seconds: float = 2.2
    final_accent_multiplier: float = 1.85
    final_whisper_multiplier: float = 1.5
    final_accent_tail_seconds: float = 3.2
    final_whisper_tail_seconds: float = 3.6
    final_stinger_tail_seconds: float = 2.8
    final_stinger_gap_seconds: float = 0.08
    final_stinger_volume: float = 0.42
    ambient_base_hz: float = 43.0
    voice_volume: float = 1.0
    fallback_silence: bool = False


class SubtitleSettings(BaseModel):
    font_file: str = ""
    font_size: int = 72
    max_chars_per_line: int = 24
    bottom_margin: int = 260
    text_color: str = "#BCA37A"
    stroke_color: str = "#090706"
    stroke_width: int = 5
    box_opacity: int = 170


class LoggingSettings(BaseModel):
    level: str = "INFO"
    file: str = "render.log"


class ProjectSettings(BaseModel):
    name: str = "Slavic Horror Engine v2"
    language: str = "Spanish"
    timezone: str = "Europe/Madrid"


class ProjectConfig(BaseModel):
    root: Path
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    providers: ProviderSettings = Field(default_factory=ProviderSettings)
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    pollinations: PollinationsSettings = Field(default_factory=PollinationsSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    story: StorySettings = Field(default_factory=StorySettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    subtitles: SubtitleSettings = Field(default_factory=SubtitleSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def load(
        cls,
        settings_path: str | Path = "settings.yaml",
        *,
        load_env: bool = True,
    ) -> "ProjectConfig":
        root = Path(settings_path).resolve().parent
        data: dict[str, Any] = {}
        path = Path(settings_path)
        if load_env:
            try:
                from dotenv import load_dotenv

                load_dotenv(root / ".env")
            except Exception:
                pass
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        config = cls(root=root, **data)
        config.resolve_paths()
        return config

    def resolve_paths(self) -> None:
        for key in ("assets", "cache", "output", "logs", "music", "fonts"):
            value = getattr(self.paths, key)
            if not value.is_absolute():
                setattr(self.paths, key, self.root / value)

    def ensure_directories(self) -> None:
        for path in (
            self.paths.assets,
            self.paths.cache,
            self.paths.output,
            self.paths.logs,
            self.paths.music,
            self.paths.fonts,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def gemini_api_key(self) -> str:
        for env_name in self.gemini.api_key_envs:
            value = os.getenv(env_name, "")
            if value:
                return value
        return ""

    @property
    def gemini_api_keys(self) -> list[str]:
        seen: set[str] = set()
        keys: list[str] = []
        for env_name in self.gemini.api_key_envs:
            value = os.getenv(env_name, "")
            if not value:
                continue
            values = [value]
            if env_name == "GEMINI_API_KEYS":
                values = [item.strip() for item in value.replace("\n", ",").replace(";", ",").split(",")]
            for item in values:
                if item and item not in seen:
                    seen.add(item)
                    keys.append(item)
        return keys

    @property
    def render_log_path(self) -> Path:
        return self.paths.logs / self.logging.file
