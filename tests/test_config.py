from pathlib import Path

from core.config import ProjectConfig


def test_project_config_loads_settings() -> None:
    config = ProjectConfig.load(Path(__file__).resolve().parents[1] / "settings.yaml")

    assert config.video.size == (1080, 1920)
    assert config.providers.image == "pollinations"
    assert config.gemini.model.startswith("gemini-2.5")
    assert config.paths.output.is_absolute()
