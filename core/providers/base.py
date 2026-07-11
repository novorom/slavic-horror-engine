from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.models.story import Story


class StoryProvider(ABC):
    @abstractmethod
    def generate_story(self, monster: str | None = None) -> Story:
        raise NotImplementedError


class ImageProvider(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, output_path: Path) -> Path:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_path: Path) -> Path:
        raise NotImplementedError
