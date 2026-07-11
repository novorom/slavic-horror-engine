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
        
        # Match narration_lines: [hook, scene1.text, scene2.text, ..., ending_question]
        # With images: [image1, image2, ..., image8, image8_reused]
        # With audio: [hook_audio, scene1_audio, ..., scene8_audio, ending_audio]
        
        # Hook scene (index 0)
        hook_audio = audio_paths[0]
        hook_image = image_paths[0]
        hook_duration = self.video_engine.audio_duration(hook_audio)
        durations.append(hook_duration)
        ambient_path, accent_path, whisper_path = self.sound_engine.prepare_scene_layers(
            0, story.hook, hook_duration, is_final_scene=False
        )
        subtitle_image = self.subtitle_engine.burn(hook_image, story.hook, 0)
        assets.append(
            SceneAssets(
                index=0,
                text=story.hook,
                image_path=hook_image,
                subtitle_image_path=subtitle_image,
                audio_path=hook_audio,
                ambient_path=ambient_path,
                accent_path=accent_path,
                whisper_path=whisper_path,
                stinger_path=None,
                duration=hook_duration,
            )
        )
        
        # Regular scenes (indices 1-8)
        for scene_index, (scene, image_path, audio_path) in enumerate(
            zip(story.scenes, image_paths[1:], audio_paths[1:len(story.scenes)+1]), start=1
        ):
            duration = self.video_engine.audio_duration(audio_path)
            durations.append(duration)
            ambient_path, accent_path, whisper_path = self.sound_engine.prepare_scene_layers(
                scene_index, scene.text, duration, is_final_scene=False
            )
            subtitle_image = self.subtitle_engine.burn(image_path, scene.text, scene_index)
            assets.append(
                SceneAssets(
                    index=scene_index,
                    text=scene.text,
                    image_path=image_path,
                    subtitle_image_path=subtitle_image,
                    audio_path=audio_path,
                    ambient_path=ambient_path,
                    accent_path=accent_path,
                    whisper_path=whisper_path,
                    stinger_path=None,
                    duration=duration,
                )
            )
        
        # Final question scene (index 9)
        final_audio = audio_paths[-1]
        final_image = image_paths[-1]
        final_duration = self.video_engine.audio_duration(final_audio)
        durations.append(final_duration)
        ambient_path, accent_path, whisper_path = self.sound_engine.prepare_scene_layers(
            9, story.ending_question, final_duration, is_final_scene=True
        )
        stinger_path = self.sound_engine.prepare_final_stinger(9, story.ending_question, final_duration)
        subtitle_image = self.subtitle_engine.burn(final_image, story.ending_question, 9)
        assets.append(
            SceneAssets(
                index=9,
                text=story.ending_question,
                image_path=final_image,
                subtitle_image_path=subtitle_image,
                audio_path=final_audio,
                ambient_path=ambient_path,
                accent_path=accent_path,
                whisper_path=whisper_path,
                stinger_path=stinger_path,
                duration=final_duration,
            )
        )

        return assets, durations
