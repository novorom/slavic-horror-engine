from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from core.config import ProjectConfig
from core.providers.base import TTSProvider


class AudioEngine:
    def __init__(self, config: ProjectConfig, provider: TTSProvider, logger: logging.Logger):
        self.config = config
        self.provider = provider
        self.logger = logger
        self.audio_dir = config.paths.cache / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def generate_voiceovers(self, lines: list[str]) -> list[Path]:
        tasks = []
        for index, line in enumerate(lines, start=1):
            output = self.audio_dir / f"scene_{index:02}.mp3"
            tasks.append(self.provider.synthesize(line, output))
        results = await asyncio.gather(*tasks)
        self.logger.info("Voiceover assets ready: %s", len(results))
        return list(results)
