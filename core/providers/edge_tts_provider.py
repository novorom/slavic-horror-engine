from __future__ import annotations

import json
import asyncio
import logging
import hashlib
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from core.config import ProjectConfig
from core.providers.base import TTSProvider


class EdgeTTSProvider(TTSProvider):
    speech_profile_revision = "pause-v1"

    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    async def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cache_meta_path = self._cache_meta_path(output_path)
        fingerprint = self._fingerprint(text)

        if output_path.exists() and cache_meta_path.exists():
            try:
                meta = json.loads(cache_meta_path.read_text(encoding="utf-8"))
                if meta.get("fingerprint") == fingerprint and self._audio_duration(output_path) > 0.3:
                    return output_path
            except Exception:
                pass

        if output_path.exists():
            output_path.unlink(missing_ok=True)
        if cache_meta_path.exists():
            cache_meta_path.unlink(missing_ok=True)

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "edge_tts",
                f"--voice={self.config.audio.voice}",
                f"--rate={self.config.audio.rate}",
                f"--pitch={self.config.audio.pitch}",
                f"--volume={self.config.audio.volume}",
                "--text",
                text,
                "--write-media",
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=90)
            if process.returncode == 0 and self._audio_duration(output_path) > 0.3:
                self._apply_voice_profile(output_path)
                self._write_cache_meta(cache_meta_path, fingerprint)
                return output_path
            self.logger.warning("edge-tts failed: %s", stderr.decode("utf-8", errors="ignore")[:300])
        except Exception as exc:
            self.logger.warning("edge-tts exception: %s", exc)

        say = shutil.which("say")
        if say:
            aiff_path = output_path.with_suffix(".aiff")
            wav_path = output_path.with_suffix(".wav")
            try:
                process = await asyncio.create_subprocess_exec(
                    say,
                    "-v",
                    self.config.audio.macos_voice,
                    "-o",
                    str(aiff_path),
                    text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=45)
                if process.returncode == 0 and aiff_path.exists() and aiff_path.stat().st_size > 0:
                    converted = self._convert_with_ffmpeg(aiff_path, wav_path)
                    if converted and self._audio_duration(wav_path) > 0.3 and wav_path.stat().st_size > 32_000:
                        self._apply_voice_profile(wav_path)
                        self._write_cache_meta(cache_meta_path, fingerprint)
                        self.logger.info("Using macOS local TTS fallback: %s", wav_path.name)
                        return wav_path
                self.logger.warning("macOS say failed: %s", stderr.decode("utf-8", errors="ignore")[:300])
            except Exception as exc:
                self.logger.warning("macOS say exception: %s", exc)

        if not self.config.audio.fallback_silence:
            raise RuntimeError(
                "TTS failed. Edge TTS did not produce valid audio, and silent fallback is disabled."
            )

        wav_path = output_path.with_suffix(".wav")
        self._write_silence(wav_path, self.config.video.fallback_duration_seconds)
        self._write_cache_meta(cache_meta_path, fingerprint)
        return wav_path

    def _fingerprint(self, text: str) -> str:
        payload = "|".join(
            [
                text,
                self.config.audio.voice,
                self.config.audio.rate,
                self.config.audio.pitch,
                self.config.audio.volume,
                self.config.audio.macos_voice,
                self.config.audio.voice_profile,
                self.speech_profile_revision,
                str(self.config.audio.voice_lowpass_hz),
                str(self.config.audio.voice_highpass_hz),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_meta_path(self, output_path: Path) -> Path:
        return output_path.with_suffix(output_path.suffix + ".meta.json")

    def _write_cache_meta(self, path: Path, fingerprint: str) -> None:
        path.write_text(json.dumps({"fingerprint": fingerprint}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _apply_voice_profile(self, output_path: Path) -> None:
        if self.config.audio.voice_profile.lower() not in {"witch", "witch_slow"}:
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            return

        temp_path = output_path.with_suffix(output_path.suffix + ".witch")
        if output_path.suffix.lower() == ".mp3":
            temp_path = output_path.with_suffix(".witch.mp3")
        elif output_path.suffix.lower() == ".wav":
            temp_path = output_path.with_suffix(".witch.wav")

        filter_chain = ",".join(
            [
                f"highpass=f={self.config.audio.voice_highpass_hz}",
                f"lowpass=f={self.config.audio.voice_lowpass_hz}",
                "acompressor=threshold=-24dB:ratio=3:attack=8:release=120",
                "volume=1.02",
            ]
        )

        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(output_path),
                "-af",
                filter_chain,
                str(temp_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not temp_path.exists() or temp_path.stat().st_size == 0:
            return
        output_path.unlink(missing_ok=True)
        temp_path.replace(output_path)

    def _write_silence(self, output_path: Path, duration: float) -> None:
        sample_rate = 44_100
        frames = int(sample_rate * duration)
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(b"\x00\x00" * frames)

    def _convert_with_ffmpeg(self, source: Path, output_path: Path) -> bool:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            return False
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-ac",
                "1",
                "-ar",
                "44100",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.logger.warning("ffmpeg TTS conversion failed: %s", result.stderr[:300])
            return False
        return output_path.exists() and output_path.stat().st_size > 0

    def _audio_duration(self, path: Path) -> float:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return 0.0
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0
