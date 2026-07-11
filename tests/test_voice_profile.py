from __future__ import annotations

import asyncio
import logging

from core.config import ProjectConfig
from core.providers.edge_tts_provider import EdgeTTSProvider


def test_voice_profile_default_is_natural_male():
    config = ProjectConfig.load("settings.yaml", load_env=False)
    assert config.audio.voice_profile == "natural"
    assert config.audio.voice == "es-ES-AlvaroNeural"
    assert config.audio.rate == "0%"
    assert config.audio.pitch == "0Hz"


def test_voice_profile_applies_when_audio_exists(monkeypatch, tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    config.audio.voice_profile = "witch_slow"
    provider = EdgeTTSProvider(config, logging.getLogger("test"))
    audio = tmp_path / "voice.mp3"
    audio.write_bytes(b"fake")

    called = {"value": False}

    def fake_run(*args, **kwargs):
        called["value"] = True
        class Result:
            returncode = 0
            stderr = ""
        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(provider, "_audio_duration", lambda path: 1.0)
    monkeypatch.setattr(provider, "_convert_with_ffmpeg", lambda source, output: True)
    monkeypatch.setattr(provider, "_write_cache_meta", lambda path, fingerprint: None)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", lambda *args, **kwargs: None)

    provider._apply_voice_profile(audio)

    assert called["value"] is True
