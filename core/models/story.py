from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class StoryScene(BaseModel):
    index: int
    text: str
    image_prompt: str


class SocialMetadata(BaseModel):
    youtube_title: str
    youtube_description: str
    instagram_caption: str
    tiktok_caption: str
    hashtags: list[str] = Field(default_factory=list)


class Story(BaseModel):
    title: str
    monster: str
    hook: str
    scenes: list[StoryScene]
    ending_question: str
    social: SocialMetadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def narration_lines(self) -> list[str]:
        return [self.hook, *[scene.text for scene in self.scenes], self.ending_question]

    def as_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
