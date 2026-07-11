from __future__ import annotations

import logging
from pathlib import Path

from core.config import ProjectConfig
from core.engines.audio_engine import AudioEngine
from core.engines.camera_engine import CameraEngine
from core.engines.image_engine import ImageEngine
from core.engines.publishing_engine import PublishingEngine
from core.engines.sound_engine import SoundEngine
from core.engines.story_engine import StoryEngine
from core.engines.subtitle_engine import SubtitleEngine
from core.engines.video_engine import VideoEngine
from core.models.assets import RenderResult, SceneAssets
from core.providers.edge_tts_provider import EdgeTTSProvider
from core.providers.gemini_provider import GeminiStoryProvider
from core.providers.pollinations_provider import PollinationsImageProvider


class SlavicHorrorPipeline:
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.story_engine = StoryEngine(config, GeminiStoryProvider(config, logger), logger)
        self.image_engine = ImageEngine(config, PollinationsImageProvider(config, logger), logger)
        self.audio_engine = AudioEngine(config, EdgeTTSProvider(config, logger), logger)
        self.sound_engine = SoundEngine(config, logger)
        self.subtitle_engine = SubtitleEngine(config, logger)
        self.video_engine = VideoEngine(config, CameraEngine(), logger)
        self.publishing_engine = PublishingEngine(config, logger)

    async def run(self) -> RenderResult:
        self.config.ensure_directories()
        self.logger.info("Starting Slavic Horror Engine v2")

        story = self.story_engine.generate()
        story_path = self.publishing_engine.write_story(story)
        social_paths = self.publishing_engine.write_social_files(story)

        image_paths = self.image_engine.generate_scene_images(story)
        thumbnail_path = self.image_engine.generate_thumbnail(story)

        lines = story.narration_lines()
        audio_paths = await self.audio_engine.generate_voiceovers(lines)

        assets, durations = self._build_scene_assets(story, image_paths, audio_paths)

        subtitle_path = self.subtitle_engine.write_srt(lines, durations)
        video_path = self.video_engine.render(assets, self.config.paths.output / "video.mp4")
        duration = sum(durations)

        result = RenderResult(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            story_path=story_path,
            metadata_path=self.config.paths.output / "metadata.json",
            youtube_path=social_paths["youtube"],
            instagram_path=social_paths["instagram"],
            tiktok_path=social_paths["tiktok"],
            hashtags_path=social_paths["hashtags"],
            subtitle_path=subtitle_path,
            duration=duration,
            scene_count=len(assets),
        )
        metadata_path = self.publishing_engine.write_metadata(story, result)
        return result.model_copy(update={"metadata_path": metadata_path})

    def _build_scene_assets(
        self,
        story,
        image_paths: list[Path],
        audio_paths: list[Path],
    ) -> tuple[list[SceneAssets], list[float]]:
        assets: list[SceneAssets] = []
        durations: list[float] = []
        render_items = list(zip(story.scenes, image_paths, audio_paths[: len(story.scenes)]))
        final_audio_path = audio_paths[-1]
        render_items.append((None, image_paths[-1], final_audio_path))

        for item_index, (scene, image_path, audio_path) in enumerate(render_items, start=1):
            is_final_question = scene is None
            text = story.ending_question if is_final_question else scene.text
            scene_index = item_index if is_final_question else scene.index
            duration = self.video_engine.audio_duration(audio_path)
            durations.append(duration)
            ambient_path, accent_path, whisper_path = self.sound_engine.prepare_scene_layers(
                scene_index,
                text,
                duration,
                is_final_scene=is_final_question,
            )
            stinger_path = (
                self.sound_engine.prepare_final_stinger(scene_index, text, duration)
                if is_final_question
                else None
            )
            subtitle_image = self.subtitle_engine.burn(image_path, text, scene_index)
            assets.append(
                SceneAssets(
                    index=scene_index,
                    text=text,
                    image_path=image_path,
                    subtitle_image_path=subtitle_image,
                    audio_path=audio_path,
                    ambient_path=ambient_path,
                    accent_path=accent_path,
                    whisper_path=whisper_path,
                    stinger_path=stinger_path,
                    duration=duration,
                )
            )

        return assets, durations
