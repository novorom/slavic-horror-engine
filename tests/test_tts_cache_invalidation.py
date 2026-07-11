from __future__ import annotations

import asyncio
import json
from pathlib import Path

from core.config import ProjectConfig
from core.providers.edge_tts_provider import EdgeTTSProvider


class _FakeProcess:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.returncode = 0

    async def communicate(self):
        self.output_path.write_bytes(b"fake-audio")
        return b"", b""


def test_tts_cache_invalidates_on_settings_change(monkeypatch, tmp_path):
    config = ProjectConfig.load("settings.yaml", load_env=False)
    logger = __import__("logging").getLogger("test")
    provider = EdgeTTSProvider(config, logger)

    output_path = tmp_path / "scene_01.mp3"
    meta_path = tmp_path / "scene_01.mp3.meta.json"
    output_path.write_bytes(b"old-audio")
    meta_path.write_text(json.dumps({"fingerprint": "old"}), encoding="utf-8")

    calls = []

    async def fake_create_subprocess_exec(*args, **kwargs):
        calls.append(args)
        return _FakeProcess(output_path)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(provider, "_audio_duration", lambda path: 1.0)

    asyncio.run(provider.synthesize("texto uno", output_path))

    assert len(calls) == 1
    meta_after = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta_after["fingerprint"] != "old"

    asyncio.run(provider.synthesize("texto uno", output_path))

    assert len(calls) == 1
