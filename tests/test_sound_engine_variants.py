from __future__ import annotations

import logging

from core.config import ProjectConfig
from core.engines.sound_engine import SoundEngine


def test_sound_engine_uses_distinct_accent_styles(tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    config.root = tmp_path
    config.paths.cache = tmp_path / "cache"
    config.paths.cache.mkdir(parents=True, exist_ok=True)
    engine = SoundEngine(config, logging.getLogger("test"))

    assert engine._accent_style(1, "La noche cae", False) == "ghoul_laugh"
    assert engine._accent_style(2, "El agua tiembla", False) == "water_plunge"
    assert engine._accent_style(3, "Alguien grita", False) == "night_scream"
    assert engine._accent_style(8, "La sombra vuelve", False) == "black_drift"
    assert engine._accent_style(9, "El final", True) == "final_abyss"


def test_sound_engine_can_build_final_stinger(tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    config.root = tmp_path
    config.paths.cache = tmp_path / "cache"
    config.paths.cache.mkdir(parents=True, exist_ok=True)
    engine = SoundEngine(config, logging.getLogger("test"))

    stinger = engine.prepare_final_stinger(8, "¿Abrirías la puerta si llama con tu voz?", 4.5)

    assert stinger.exists()
    assert stinger.stat().st_size > 1000
