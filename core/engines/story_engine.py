from __future__ import annotations

import logging
import random

from core.config import ProjectConfig
from core.models.story import Story
from core.providers.base import StoryProvider


class StoryEngine:
    def __init__(self, config: ProjectConfig, provider: StoryProvider, logger: logging.Logger):
        self.config = config
        self.provider = provider
        self.logger = logger

    def generate(self, monster: str | None = None) -> Story:
        monster = monster or random.choice(self.config.story.monsters)
        self.logger.info("Generating story about %s", monster)
        story = self.provider.generate_story(monster)
        self.logger.info("Story ready: %s (%s scenes)", story.title, len(story.scenes))
        return story
