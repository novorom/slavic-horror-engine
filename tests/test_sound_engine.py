from __future__ import annotations

import logging

from core.config import ProjectConfig
from core.engines.sound_engine import SoundEngine


def test_sound_engine_writes_bed_and_accent(tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    config.root = tmp_path
    config.paths.cache = tmp_path / "cache"
    config.paths.cache.mkdir(parents=True, exist_ok=True)
    engine = SoundEngine(config, logging.getLogger("test"))

    ambient, accent, whisper = engine.prepare_scene_layers(1, "La noche cae sobre el pueblo", 4.0)

    assert ambient.exists()
    assert accent.exists()
    assert whisper is None
    assert ambient.stat().st_size > 1000
    assert accent.stat().st_size > 1000
