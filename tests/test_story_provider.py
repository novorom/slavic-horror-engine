from core.config import ProjectConfig
from core.providers.gemini_provider import GeminiStoryProvider
from core.utils.logging import configure_logging


def test_fallback_story_is_valid(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config = ProjectConfig.load("settings.yaml")
    logger = configure_logging(config)
    provider = GeminiStoryProvider(config, logger)

    story = provider.generate_story("Leshy")

    assert story.monster == "Leshy"
    assert len(story.scenes) >= 4
    assert story.social.youtube_title
    assert story.ending_question.endswith("?")
    assert story.narration_lines()[-1] == story.ending_question
