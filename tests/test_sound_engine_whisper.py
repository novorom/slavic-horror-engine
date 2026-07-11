from __future__ import annotations

import logging

from core.config import ProjectConfig
from core.engines.sound_engine import SoundEngine


def test_sound_engine_adds_whisper_on_tense_scene(tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    config.root = tmp_path
    config.paths.cache = tmp_path / "cache"
    config.paths.cache.mkdir(parents=True, exist_ok=True)
    engine = SoundEngine(config, logging.getLogger("test"))

    ambient, accent, whisper = engine.prepare_scene_layers(6, "No mires la puerta en la niebla", 4.0)

    assert ambient.exists()
    assert accent.exists()
    assert whisper is not None
    assert whisper.exists()
