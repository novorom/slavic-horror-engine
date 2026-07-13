from __future__ import annotations

import hashlib
import logging
import math
import json
import wave
from pathlib import Path

import numpy as np

from core.config import ProjectConfig


class SoundEngine:
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.sound_dir = config.paths.cache / "sound"
        self.sound_dir.mkdir(parents=True, exist_ok=True)

    def prepare_scene_layers(
        self,
        scene_index: int,
        text: str,
        duration: float,
        *,
        is_final_scene: bool = False,
    ) -> tuple[Path, Path, Path | None]:
        ambient_path = self.sound_dir / f"ambient_{scene_index:02}.wav"
        accent_path = self.sound_dir / f"accent_{scene_index:02}.wav"
        whisper_path = self.sound_dir / f"whisper_{scene_index:02}.wav"
        ambient_fingerprint = self._fingerprint("ambient", scene_index, text, duration, is_final_scene)
        accent_style = self._accent_style(scene_index, text, is_final_scene)
        accent_fingerprint = self._fingerprint("accent", scene_index, text, duration, is_final_scene, accent_style)
        whisper_enabled = self._scene_needs_whisper(text, scene_index)
        whisper_fingerprint = self._fingerprint("whisper", scene_index, text, duration, is_final_scene)

        self._ensure_sound_file(
            ambient_path,
            ambient_fingerprint,
            lambda path: self._write_ambient_bed(path, duration, scene_index, text, is_final_scene),
        )
        self._ensure_sound_file(
            accent_path,
            accent_fingerprint,
            lambda path: self._write_accent_fx(path, self.config.audio.accent_tail_seconds, scene_index, text, accent_style, is_final_scene),
        )
        if whisper_enabled:
            whisper_tail = (
                self.config.audio.final_whisper_tail_seconds
                if is_final_scene
                else self.config.audio.whisper_tail_seconds * 1.05
            )
            self._ensure_sound_file(
                whisper_path,
                whisper_fingerprint,
                lambda path: self._write_whisper_layer(path, whisper_tail, scene_index, text, is_final_scene),
            )

        return ambient_path, accent_path, whisper_path if whisper_enabled else None

    def prepare_final_stinger(self, scene_index: int, text: str, duration: float) -> Path:
        stinger_path = self.sound_dir / f"stinger_{scene_index:02}.wav"
        stinger_fingerprint = self._fingerprint("stinger", scene_index, text, duration, True, "final_wail")
        self._ensure_sound_file(
            stinger_path,
            stinger_fingerprint,
            lambda path: self._write_stinger_fx(path, self.config.audio.final_stinger_tail_seconds, scene_index, text),
        )
        return stinger_path

    def _fingerprint(self, kind: str, scene_index: int, text: str, duration: float, is_final_scene: bool, variant: str = "") -> str:
        payload = "|".join(
            [
                kind,
                str(scene_index),
                text,
                f"{duration:.3f}",
                str(is_final_scene),
                variant,
                str(self.config.audio.music_volume),
                str(self.config.audio.accent_volume),
                str(self.config.audio.whisper_volume),
                str(self.config.audio.final_accent_multiplier),
                str(self.config.audio.final_whisper_multiplier),
                str(self.config.audio.final_stinger_tail_seconds),
                str(self.config.audio.final_stinger_gap_seconds),
                str(self.config.audio.final_stinger_volume),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _ensure_sound_file(self, output_path: Path, fingerprint: str, writer) -> None:
        meta_path = output_path.with_suffix(output_path.suffix + ".meta.json")
        if output_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("fingerprint") == fingerprint and output_path.stat().st_size > 1000:
                    return
            except Exception:
                pass
        output_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        writer(output_path)
        if output_path.exists():
            meta_path.write_text(json.dumps({"fingerprint": fingerprint}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_ambient_bed(self, output_path: Path, duration: float, scene_index: int, text: str, is_final_scene: bool) -> None:
        sample_rate = 44_100
        frames = max(int(sample_rate * duration), sample_rate)
        t = np.linspace(0.0, duration, frames, endpoint=False)
        seed = int(hashlib.sha256(f"{scene_index}:{text}".encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)

        base_hz = self.config.audio.ambient_base_hz
        drone = (
            0.26 * np.sin(2 * math.pi * base_hz * t)
            + 0.14 * np.sin(2 * math.pi * (base_hz * 1.42) * t)
            + 0.08 * np.sin(2 * math.pi * (base_hz * 2.07) * t)
        )
        hiss = 0.025 * rng.normal(size=frames)
        pulse_rate = 0.06 + (0.02 if is_final_scene else 0.0)
        pulse = 0.48 + 0.52 * np.sin(2 * math.pi * pulse_rate * t + scene_index)
        envelope = self._ducking_envelope(duration, sample_rate)
        final_boost = 1.12 if is_final_scene else 1.0
        samples = (drone * pulse + hiss) * envelope * self.config.audio.music_volume * final_boost
        self._write_pcm_wav(output_path, samples, sample_rate)

    def _write_accent_fx(self, output_path: Path, duration: float, scene_index: int, text: str, style: str, is_final_scene: bool) -> None:
        sample_rate = 44_100
        dur = duration * (self.config.audio.final_accent_tail_seconds / self.config.audio.accent_tail_seconds if is_final_scene else 1.0)
        frames = max(int(sample_rate * dur), sample_rate // 2)
        t = np.linspace(0.0, dur, frames, endpoint=False)
        seed = int(hashlib.sha256(f"accent:{style}:{scene_index}:{text}".encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)

        samples = self._accent_wave(style, t, rng, scene_index, is_final_scene)
        envelope = self._accent_envelope(dur, sample_rate)
        volume = self.config.audio.accent_volume * (self.config.audio.final_accent_multiplier if is_final_scene else 1.0)
        samples = samples * envelope * volume
        self._write_pcm_wav(output_path, samples, sample_rate)

    def _write_whisper_layer(self, output_path: Path, duration: float, scene_index: int, text: str, is_final_scene: bool) -> None:
        sample_rate = 44_100
        dur = duration * (1.4 if is_final_scene else 1.0)
        frames = max(int(sample_rate * dur), sample_rate // 2)
        t = np.linspace(0.0, dur, frames, endpoint=False)
        seed = int(hashlib.sha256(f"whisper:{scene_index}:{text}:{is_final_scene}".encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        hiss = rng.normal(size=frames)
        flutter = 0.5 + 0.5 * np.sin(2 * math.pi * (3.2 + (0.7 if is_final_scene else 0.0)) * t + scene_index)
        breath = np.maximum(0.0, np.sin(2 * math.pi * (0.85 + (0.2 if is_final_scene else 0.0)) * t))
        envelope = self._accent_envelope(dur, sample_rate)
        volume = self.config.audio.whisper_volume * (self.config.audio.final_whisper_multiplier if is_final_scene else 1.0)
        samples = (0.34 * hiss * flutter + 0.12 * breath) * envelope * volume
        self._write_pcm_wav(output_path, samples, sample_rate)

    def _write_stinger_fx(self, output_path: Path, duration: float, scene_index: int, text: str) -> None:
        sample_rate = 44_100
        dur = self.config.audio.final_stinger_tail_seconds
        frames = max(int(sample_rate * dur), sample_rate // 2)
        t = np.linspace(0.0, dur, frames, endpoint=False)
        seed = int(hashlib.sha256(f"stinger:{scene_index}:{text}".encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)

        # Enhanced scream for final scene
        rise = np.linspace(320.0, 1800.0, frames)
        scream = (
            0.62 * np.sin(2 * math.pi * rise * t)
            + 0.28 * np.sin(2 * math.pi * (rise * 2.1) * t)
            + 0.35 * np.sin(2 * math.pi * (rise * 0.5) * t)
            + 0.32 * rng.normal(size=frames)
        )
        tremor = 0.55 + 0.45 * np.sin(2 * math.pi * 12.0 * t)
        impact = np.zeros(frames, dtype=np.float32)
        impact_start = max(frames - int(sample_rate * min(dur, 0.42)), 0)
        if impact_start < frames:
            impact[impact_start:] = np.linspace(0.0, 1.0, frames - impact_start)
        envelope = self._fade_envelope(dur, sample_rate, fade_in=0.02, fade_out=0.92)
        samples = scream * tremor * impact * envelope * self.config.audio.final_stinger_volume
        samples += 0.08 * rng.normal(size=frames) * envelope
        self._write_pcm_wav(output_path, samples, sample_rate)

    def _fade_envelope(self, duration: float, sample_rate: int, fade_in: float, fade_out: float) -> np.ndarray:
        frames = max(int(sample_rate * duration), sample_rate)
        env = np.ones(frames, dtype=np.float32)
        fade_in_frames = min(int(sample_rate * fade_in), frames)
        fade_out_frames = min(int(sample_rate * fade_out), frames)
        if fade_in_frames > 1:
            env[:fade_in_frames] = np.linspace(0.0, 1.0, fade_in_frames)
        if fade_out_frames > 1:
            env[-fade_out_frames:] *= np.linspace(1.0, 0.0, fade_out_frames)
        return env

    def _ducking_envelope(self, duration: float, sample_rate: int) -> np.ndarray:
        frames = max(int(sample_rate * duration), sample_rate)
        env = np.full(frames, self.config.audio.voice_ducking_floor, dtype=np.float32)
        rise_frames = max(int(sample_rate * min(duration, self.config.audio.voice_ducking_rise)), 1)
        if rise_frames > 1:
            env[:rise_frames] = np.linspace(self.config.audio.voice_ducking_floor, 1.0, rise_frames)
        return env

    def _accent_envelope(self, duration: float, sample_rate: int) -> np.ndarray:
        frames = max(int(sample_rate * duration), sample_rate // 2)
        env = np.zeros(frames, dtype=np.float32)
        tail_frames = max(int(sample_rate * min(duration, self.config.audio.accent_tail_seconds)), 1)
        start = max(frames - tail_frames, 0)
        if start < frames:
            attack = max(int(tail_frames * 0.45), 1)
            sustain = max(tail_frames - attack, 1)
            env[start : start + attack] = np.linspace(0.0, 1.0, attack)
            if start + attack < frames:
                env[start + attack : start + attack + sustain] = np.linspace(1.0, 0.35, min(sustain, frames - (start + attack)))
        return env

    def _accent_style(self, scene_index: int, text: str, is_final_scene: bool) -> str:
        if is_final_scene:
            return "final_abyss"
        palette = [
            "ghoul_laugh",
            "water_plunge",
            "night_scream",
            "chain_drag",
            "shriek",
            "bone_rattle",
            "breath_rush",
            "black_drift",
            "wood_creak",
            "metal_scrape",
            "sub_boom",
            "reverse_swell",
            "bone_knock",
            "bell_dread",
            "breath_snap",
            "blood_drip",
            "ghost_whisper",
            "heart_beat",
            "wind_howl",
            "thunder_crack",
            "door_slam",
            "glass_break",
            "footsteps",
            "breathing_heavy",
            "scream_long",
            "whisper_chant",
            "splash_water",
            "rustle_leaves",
            "owl_hoot",
            "wolf_howl",
            "fire_crackle",
            "ice_crack",
            "stone_drag",
            "metal_clang",
        ]
        if scene_index <= 0:
            scene_index = 1
        return palette[(scene_index - 1) % len(palette)]

    def _accent_wave(self, style: str, t: np.ndarray, rng: np.random.Generator, scene_index: int, is_final_scene: bool) -> np.ndarray:
        if style == "wood_creak":
            base = 150.0 - scene_index * 4.0
            sweep = np.linspace(1.0, 0.45, len(t))
            return 0.52 * np.sin(2 * math.pi * base * sweep * t) + 0.12 * rng.normal(size=len(t))
        if style == "ghoul_laugh":
            bursts = np.zeros_like(t)
            centers = [0.12, 0.28, 0.48, 0.69, 0.86]
            for i, center in enumerate(centers):
                width = t[-1] * (0.016 + i * 0.001)
                idx = np.abs(t - (t[-1] * center)) < width
                if idx.any():
                    tone = 210.0 + 48.0 * (i % 2)
                    bursts[idx] += 0.34 * np.sin(2 * math.pi * tone * t[idx])
                    bursts[idx] += 0.18 * np.sin(2 * math.pi * (tone * 1.9) * t[idx])
            return bursts + 0.08 * rng.normal(size=len(t))
        if style == "water_plunge":
            drop = np.exp(-2.2 * (t / max(t[-1], 0.001)))
            splash = 0.30 * np.sin(2 * math.pi * 36.0 * t) + 0.22 * np.sin(2 * math.pi * 71.0 * t)
            bubbles = 0.18 * rng.normal(size=len(t))
            return (splash + bubbles) * drop
        if style == "night_scream":
            sweep = np.linspace(180.0, 980.0, len(t))
            body = 0.44 * np.sin(2 * math.pi * sweep * t)
            edge = 0.25 * np.sin(2 * math.pi * (sweep * 1.55) * t)
            return (body + edge + 0.16 * rng.normal(size=len(t))) * np.linspace(0.12, 1.0, len(t))
        if style == "chain_drag":
            grit = 0.28 * rng.normal(size=len(t))
            scrape = 0.26 * np.sin(2 * math.pi * (290.0 - 120.0 * (t / max(t[-1], 0.001))) * t)
            metallic = 0.16 * np.sin(2 * math.pi * 920.0 * t)
            return grit + scrape + metallic
        if style == "shriek":
            sweep = np.linspace(720.0, 1600.0, len(t))
            return (0.34 * np.sin(2 * math.pi * sweep * t) + 0.24 * rng.normal(size=len(t))) * np.linspace(0.2, 1.0, len(t))
        if style == "bone_rattle":
            knocks = np.zeros_like(t)
            hits = (0.18, 0.38, 0.56, 0.74, 0.91)
            for i, center in enumerate(hits):
                idx = np.abs(t - (t[-1] * center)) < (t[-1] * 0.018)
                knocks[idx] += 0.66 * np.sin(2 * math.pi * (88.0 - 3.0 * i) * t[idx])
            return knocks + 0.06 * rng.normal(size=len(t))
        if style == "breath_rush":
            inhale = np.maximum(0.0, np.sin(2 * math.pi * 0.72 * t))
            exhale = np.maximum(0.0, np.sin(2 * math.pi * 1.35 * t + 0.4))
            hiss = 0.22 * rng.normal(size=len(t))
            return 0.32 * inhale + 0.18 * exhale + hiss
        if style == "metal_scrape":
            burst = np.zeros_like(t)
            burst[t > t[-1] * 0.15] = 0.45
            burst[t > t[-1] * 0.55] = 0.2
            return 0.42 * rng.normal(size=len(t)) * burst + 0.18 * np.sin(2 * math.pi * (320 - 140 * (t / max(t[-1], 0.001))) * t)
        if style == "sub_boom":
            freq = 48.0 if not is_final_scene else 30.0
            decay = np.exp(-2.8 * (t / max(t[-1], 0.001)))
            return (0.7 * np.sin(2 * math.pi * freq * t) + 0.18 * np.sin(2 * math.pi * 2 * freq * t)) * decay
        if style == "reverse_swell":
            reverse_env = np.linspace(0.15, 1.0, len(t))
            return (0.34 * rng.normal(size=len(t)) + 0.22 * np.sin(2 * math.pi * 95.0 * t)) * reverse_env
        if style == "bone_knock":
            knocks = np.zeros_like(t)
            for center, freq in ((0.22, 92.0), (0.48, 88.0), (0.74, 84.0), (0.92, 80.0)):
                idx = np.abs(t - (t[-1] * center)) < (t[-1] * 0.022)
                knocks[idx] += 0.72 * np.sin(2 * math.pi * freq * t[idx])
            return knocks + 0.08 * rng.normal(size=len(t))
        if style == "bell_dread":
            bell = 0.26 * np.sin(2 * math.pi * 610.0 * t) + 0.26 * np.sin(2 * math.pi * 616.0 * t)
            return bell * np.exp(-1.8 * (t / max(t[-1], 0.001)))
        if style == "breath_snap":
            inhale = np.maximum(0.0, np.sin(2 * math.pi * 0.95 * t))
            gasp = np.maximum(0.0, np.sin(2 * math.pi * 2.9 * t))
            return 0.34 * inhale + 0.18 * gasp + 0.14 * rng.normal(size=len(t))
        if style == "black_drift":
            drift = 0.28 * np.sin(2 * math.pi * 28.0 * t) + 0.16 * np.sin(2 * math.pi * 57.0 * t)
            return drift + 0.1 * rng.normal(size=len(t))
        if style == "final_abyss":
            return (
                0.65 * np.sin(2 * math.pi * 24.0 * t)
                + 0.24 * np.sin(2 * math.pi * 17.0 * t)
                + 0.22 * rng.normal(size=len(t))
                + 0.18 * np.sin(2 * math.pi * (160.0 - 120.0 * (t / max(t[-1], 0.001))) * t)
                + 0.15 * np.maximum(0.0, np.sin(2 * math.pi * 1.2 * t))
            )
        if style == "final_wail":
            sweep = np.linspace(520.0, 140.0, len(t))
            return (
                0.58 * np.sin(2 * math.pi * sweep * t)
                + 0.28 * np.sin(2 * math.pi * (sweep * 1.86) * t)
                + 0.26 * rng.normal(size=len(t))
                + 0.20 * np.maximum(0.0, np.sin(2 * math.pi * 5.5 * t))
            )
        if style == "blood_drip":
            drip_times = np.linspace(0.1, 0.9, 8)
            drops = np.zeros_like(t)
            for drip_time in drip_times:
                idx = np.abs(t - (t[-1] * drip_time)) < (t[-1] * 0.03)
                if idx.any():
                    freq = 180.0 + 40.0 * rng.random()
                    drops[idx] += 0.45 * np.sin(2 * math.pi * freq * t[idx]) * np.exp(-10.0 * (t[idx] - t[idx][0]))
            return drops + 0.06 * rng.normal(size=len(t))
        if style == "ghost_whisper":
            whisper_freq = np.linspace(400.0, 600.0, len(t))
            whisper_mod = 0.5 + 0.5 * np.sin(2 * math.pi * 2.5 * t)
            return (
                0.28 * np.sin(2 * math.pi * whisper_freq * t) * whisper_mod
                + 0.18 * rng.normal(size=len(t))
                + 0.12 * np.sin(2 * math.pi * 120.0 * t)
            )
        if style == "heart_beat":
            beat_times = [0.15, 0.35, 0.55, 0.75, 0.90]
            beats = np.zeros_like(t)
            for beat_time in beat_times:
                idx = np.abs(t - (t[-1] * beat_time)) < (t[-1] * 0.04)
                if idx.any():
                    beats[idx] += 0.65 * np.sin(2 * math.pi * 85.0 * t[idx]) * np.exp(-15.0 * (t[idx] - t[idx][0]))
            return beats + 0.04 * rng.normal(size=len(t))
        if style == "wind_howl":
            wind_freq = np.linspace(200.0, 800.0, len(t))
            wind_mod = 0.3 + 0.7 * np.sin(2 * math.pi * 1.8 * t)
            return (
                0.42 * np.sin(2 * math.pi * wind_freq * t) * wind_mod
                + 0.22 * rng.normal(size=len(t))
                + 0.15 * np.sin(2 * math.pi * 45.0 * t)
            )
        if style == "thunder_crack":
            crack = np.zeros_like(t)
            crack[t > t[-1] * 0.3] = 0.8
            crack[t > t[-1] * 0.35] = 0.4
            return (
                0.55 * rng.normal(size=len(t)) * crack
                + 0.35 * np.sin(2 * math.pi * 60.0 * t) * np.exp(-3.0 * (t / max(t[-1], 0.001)))
            )
        if style == "door_slam":
            slam_time = 0.6
            slam_idx = np.abs(t - (t[-1] * slam_time)) < (t[-1] * 0.05)
            slam = np.zeros_like(t)
            if slam_idx.any():
                slam[slam_idx] += 0.75 * np.sin(2 * math.pi * 120.0 * t[slam_idx]) * np.exp(-8.0 * (t[slam_idx] - t[slam_idx][0]))
            return slam + 0.08 * rng.normal(size=len(t))
        if style == "glass_break":
            glass_times = [0.25, 0.45, 0.65]
            glass = np.zeros_like(t)
            for glass_time in glass_times:
                idx = np.abs(t - (t[-1] * glass_time)) < (t[-1] * 0.02)
                if idx.any():
                    freq = 2000.0 + 500.0 * rng.random()
                    glass[idx] += 0.55 * np.sin(2 * math.pi * freq * t[idx]) * np.exp(-20.0 * (t[idx] - t[idx][0]))
            return glass + 0.1 * rng.normal(size=len(t))
        if style == "footsteps":
            step_times = [0.1, 0.25, 0.4, 0.55, 0.7, 0.85]
            steps = np.zeros_like(t)
            for step_time in step_times:
                idx = np.abs(t - (t[-1] * step_time)) < (t[-1] * 0.025)
                if idx.any():
                    steps[idx] += 0.4 * np.sin(2 * math.pi * 150.0 * t[idx]) * np.exp(-12.0 * (t[idx] - t[idx][0]))
            return steps + 0.05 * rng.normal(size=len(t))
        if style == "breathing_heavy":
            inhale = np.maximum(0.0, np.sin(2 * math.pi * 0.5 * t))
            exhale = np.maximum(0.0, np.sin(2 * math.pi * 1.0 * t + 0.5))
            hiss = 0.15 * rng.normal(size=len(t))
            return 0.35 * inhale + 0.25 * exhale + hiss
        if style == "scream_long":
            sweep = np.linspace(400.0, 1200.0, len(t))
            scream_env = np.concatenate([np.linspace(0.0, 1.0, len(t) // 3), np.ones(len(t) // 3), np.linspace(1.0, 0.0, len(t) - 2 * len(t) // 3)])
            return (
                (0.45 * np.sin(2 * math.pi * sweep * t) + 0.25 * np.sin(2 * math.pi * (sweep * 1.5) * t))
                * scream_env
                + 0.18 * rng.normal(size=len(t))
            )
        if style == "whisper_chant":
            chant_freq = np.linspace(300.0, 500.0, len(t))
            chant_mod = 0.4 + 0.6 * np.sin(2 * math.pi * 3.0 * t)
            return (
                0.32 * np.sin(2 * math.pi * chant_freq * t) * chant_mod
                + 0.18 * np.sin(2 * math.pi * 150.0 * t)
                + 0.12 * rng.normal(size=len(t))
            )
        if style == "splash_water":
            splash = np.zeros_like(t)
            splash[t > t[-1] * 0.4] = 1.0
            splash = splash * np.exp(-2.5 * (t / max(t[-1], 0.001)))
            water = 0.38 * np.sin(2 * math.pi * 80.0 * t) + 0.25 * np.sin(2 * math.pi * 150.0 * t)
            bubbles = 0.18 * rng.normal(size=len(t))
            return (water + bubbles) * splash
        if style == "rustle_leaves":
            rustle_freq = np.linspace(400.0, 800.0, len(t))
            rustle_mod = 0.5 + 0.5 * np.sin(2 * math.pi * 4.0 * t)
            return (
                0.35 * np.sin(2 * math.pi * rustle_freq * t) * rustle_mod
                + 0.22 * rng.normal(size=len(t))
                + 0.15 * np.sin(2 * math.pi * 200.0 * t)
            )
        if style == "owl_hoot":
            hoot_times = [0.2, 0.6]
            hoots = np.zeros_like(t)
            for hoot_time in hoot_times:
                idx = np.abs(t - (t[-1] * hoot_time)) < (t[-1] * 0.08)
                if idx.any():
                    hoot_freq = 400.0 + 50.0 * rng.random()
                    hoots[idx] += 0.5 * np.sin(2 * math.pi * hoot_freq * t[idx]) * np.exp(-5.0 * (t[idx] - t[idx][0]))
            return hoots + 0.08 * rng.normal(size=len(t))
        if style == "wolf_howl":
            howl_freq = np.linspace(300.0, 600.0, len(t))
            howl_env = np.concatenate([np.linspace(0.0, 1.0, len(t) // 4), np.ones(len(t) // 2), np.linspace(1.0, 0.0, len(t) - 3 * len(t) // 4)])
            return (
                0.48 * np.sin(2 * math.pi * howl_freq * t) * howl_env
                + 0.22 * np.sin(2 * math.pi * (howl_freq * 1.3) * t) * howl_env
                + 0.15 * rng.normal(size=len(t))
            )
        if style == "fire_crackle":
            crackle_times = np.linspace(0.1, 0.9, 15)
            crackles = np.zeros_like(t)
            for crackle_time in crackle_times:
                idx = np.abs(t - (t[-1] * crackle_time)) < (t[-1] * 0.015)
                if idx.any():
                    freq = 800.0 + 400.0 * rng.random()
                    crackles[idx] += 0.35 * np.sin(2 * math.pi * freq * t[idx]) * np.exp(-25.0 * (t[idx] - t[idx][0]))
            return crackles + 0.12 * rng.normal(size=len(t))
        if style == "ice_crack":
            crack = np.zeros_like(t)
            crack[t > t[-1] * 0.5] = 1.0
            crack = crack * np.exp(-4.0 * (t / max(t[-1], 0.001)))
            ice = 0.55 * np.sin(2 * math.pi * 2000.0 * t) + 0.35 * np.sin(2 * math.pi * 1500.0 * t)
            return ice * crack + 0.08 * rng.normal(size=len(t))
        if style == "stone_drag":
            drag_freq = np.linspace(100.0, 200.0, len(t))
            grind = 0.38 * np.sin(2 * math.pi * drag_freq * t) + 0.22 * rng.normal(size=len(t))
            scrape = 0.28 * np.sin(2 * math.pi * 400.0 * t) * np.linspace(0.0, 1.0, len(t))
            return grind + scrape
        if style == "metal_clang":
            clang_times = [0.3, 0.7]
            clangs = np.zeros_like(t)
            for clang_time in clang_times:
                idx = np.abs(t - (t[-1] * clang_time)) < (t[-1] * 0.03)
                if idx.any():
                    clang_freq = 800.0 + 200.0 * rng.random()
                    clangs[idx] += 0.65 * np.sin(2 * math.pi * clang_freq * t[idx]) * np.exp(-10.0 * (t[idx] - t[idx][0]))
            return clangs + 0.08 * rng.normal(size=len(t))
        return 0.25 * rng.normal(size=len(t))

    def _scene_needs_whisper(self, text: str, scene_index: int) -> bool:
        lowered = text.lower()
        keywords = (
            "susurro",
            "sombra",
            "bosque",
            "mira",
            "mirar",
            "voz",
            "ojos",
            "puerta",
            "hielo",
            "pozo",
            "niebla",
            "oscuro",
            "oscura",
            "no mires",
            "respira",
            "respirar",
            "detrás",
            "detras",
        )
        return any(word in lowered for word in keywords) or scene_index >= 5

    def _write_pcm_wav(self, output_path: Path, samples: np.ndarray, sample_rate: int) -> None:
        clipped = np.clip(samples, -1.0, 1.0)
        pcm = (clipped * 32767).astype(np.int16)
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())
