from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PIL import Image

from core.config import ProjectConfig
from core.engines.camera_engine import CameraEngine
from core.models.assets import SceneAssets
from core.utils.image import cover_resize


class VideoEngine:
    def __init__(self, config: ProjectConfig, camera: CameraEngine, logger: logging.Logger):
        self.config = config
        self.camera = camera
        self.logger = logger

    def audio_duration(self, audio_path: Path) -> float:
        import moviepy as mp

        clip = mp.AudioFileClip(str(audio_path))
        try:
            return float(clip.duration or self.config.video.fallback_duration_seconds)
        finally:
            clip.close()

    def render(self, assets: list[SceneAssets], output_path: Path) -> Path:
        import moviepy as mp

        output_path.parent.mkdir(parents=True, exist_ok=True)
        clips = []
        audio_clips = []
        mixed_audio_clips = []
        for asset in assets:
            audio = mp.AudioFileClip(str(asset.audio_path))
            audio_clips.append(audio)
            duration = max(float(audio.duration or asset.duration), 1.0)
            audio_layers = [audio]
            if asset.ambient_path:
                ambient = mp.AudioFileClip(str(asset.ambient_path))
                audio_layers.append(ambient)
                audio_clips.append(ambient)
            else:
                ambient = None
            if asset.accent_path:
                accent = mp.AudioFileClip(str(asset.accent_path)).with_start(max(duration - self.config.audio.accent_tail_seconds, 0.0))
                audio_layers.append(accent)
                audio_clips.append(accent)
            else:
                accent = None
            if asset.whisper_path:
                whisper = mp.AudioFileClip(str(asset.whisper_path)).with_start(max(duration - self.config.audio.whisper_tail_seconds, 0.0))
                audio_layers.append(whisper)
                audio_clips.append(whisper)
            else:
                whisper = None
            clip_duration = duration
            if asset.stinger_path:
                stinger = mp.AudioFileClip(str(asset.stinger_path))
                stinger_start = duration + self.config.audio.final_stinger_gap_seconds
                audio_layers.append(stinger.with_start(stinger_start))
                audio_clips.append(stinger)
                clip_duration = max(clip_duration, stinger_start + float(stinger.duration or self.config.audio.final_stinger_tail_seconds))
            else:
                stinger = None
            video = self._animated_image_clip(asset.subtitle_image_path, asset.index, clip_duration)
            mixed_audio = mp.CompositeAudioClip(audio_layers)
            mixed_audio_clips.append(mixed_audio)
            clips.append(video.with_audio(mixed_audio))

        final = mp.concatenate_videoclips(clips, method="compose")
        self.logger.info("Writing video to %s", output_path)
        final.write_videofile(
            str(output_path),
            fps=self.config.video.fps,
            codec=self.config.video.codec,
            audio_codec=self.config.video.audio_codec,
            temp_audiofile=str(output_path.with_suffix(".temp-audio.m4a")),
            remove_temp=True,
            preset=self.config.video.preset,
            ffmpeg_params=[
                "-movflags",
                "+faststart",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(self.config.video.crf),
            ],
            logger=None,
        )

        final.close()
        for clip in audio_clips:
            try:
                clip.close()
            except Exception:
                pass
        for clip in mixed_audio_clips:
            try:
                clip.close()
            except Exception:
                pass
        for clip in clips:
            clip.close()
        return output_path

    def _animated_image_clip(self, image_path: Path, scene_index: int, duration: float):
        import moviepy as mp

        target_width, target_height = self.config.video.size
        image = Image.open(image_path).convert("RGB")
        if image.size != self.config.video.size:
            image = cover_resize(image, self.config.video.size)
        move = self.camera.move_for_scene(scene_index)

        def frame_function(t: float):
            zoom, cx, cy = self.camera.interpolate(move, t, duration)
            stretch = self.config.video.horizontal_stretch
            new_width = max(int(target_width * zoom * stretch), target_width)
            new_height = max(int(target_height * zoom), target_height)
            frame = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = int((new_width - target_width) * cx)
            top = int((new_height - target_height) * cy)
            left = min(max(left, 0), new_width - target_width)
            top = min(max(top, 0), new_height - target_height)
            frame = frame.crop((left, top, left + target_width, top + target_height))
            return np.array(frame)

        clip = mp.VideoClip(frame_function=frame_function, duration=duration)
        return clip.with_fps(self.config.video.fps)
