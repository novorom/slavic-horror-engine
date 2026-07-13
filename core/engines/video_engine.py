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
            
            # Calculate total sound duration after voice ends
            sound_delay = 0.0
            
            if asset.ambient_path:
                ambient = mp.AudioFileClip(str(asset.ambient_path))
                ambient_duration = float(ambient.duration or 0.0)
                audio_layers.append(ambient.with_start(duration))
                audio_clips.append(ambient)
                sound_delay = max(sound_delay, ambient_duration)
            else:
                ambient = None
            
            if asset.accent_path:
                accent = mp.AudioFileClip(str(asset.accent_path))
                accent_duration = float(accent.duration or 0.0)
                audio_layers.append(accent.with_start(duration))
                audio_clips.append(accent)
                sound_delay = max(sound_delay, accent_duration)
            else:
                accent = None
            
            if asset.whisper_path:
                whisper = mp.AudioFileClip(str(asset.whisper_path))
                whisper_duration = float(whisper.duration or 0.0)
                audio_layers.append(whisper.with_start(duration))
                audio_clips.append(whisper)
                sound_delay = max(sound_delay, whisper_duration)
            else:
                whisper = None
            
            clip_duration = duration + sound_delay
            if asset.stinger_path:
                stinger = mp.AudioFileClip(str(asset.stinger_path))
                stinger_start = clip_duration + self.config.audio.final_stinger_gap_seconds
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
            
            # Add watermark if enabled
            if hasattr(self.config, 'watermark') and self.config.watermark.enabled:
                frame = self._add_watermark(frame)
                
            return np.array(frame)

        clip = mp.VideoClip(frame_function=frame_function, duration=duration)
        return clip.with_fps(self.config.video.fps)

    def _add_watermark(self, frame: Image.Image) -> Image.Image:
        """Add watermark to frame."""
        from PIL import ImageDraw, ImageFont
        
        try:
            draw = ImageDraw.Draw(frame)
            
            # Watermark settings
            position = getattr(self.config.watermark, 'position', 'bottom_right')
            opacity = getattr(self.config.watermark, 'opacity', 0.7)
            size_ratio = getattr(self.config.watermark, 'size', 0.08)
            
            # Calculate watermark size
            frame_width, frame_height = frame.size
            watermark_size = int(min(frame_width, frame_height) * size_ratio)
            
            # Simple text watermark
            text = "Cuentos de Terror Eslavo"
            
            # Try to use a font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(watermark_size / 4))
            except:
                font = ImageFont.load_default()
            
            # Calculate position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            margin = 20
            if position == 'bottom_right':
                x = frame_width - text_width - margin
                y = frame_height - text_height - margin
            elif position == 'bottom_left':
                x = margin
                y = frame_height - text_height - margin
            elif position == 'top_right':
                x = frame_width - text_width - margin
                y = margin
            else:  # top_left
                x = margin
                y = margin
            
            # Create semi-transparent text
            watermark_color = (255, 255, 255, int(255 * opacity))
            
            # Draw shadow
            draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, int(255 * opacity)))
            # Draw text
            draw.text((x, y), text, font=font, fill=watermark_color)
            
        except Exception as e:
            self.logger.warning(f"Error adding watermark: {e}")
        
        return frame
