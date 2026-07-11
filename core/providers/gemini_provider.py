from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from typing import Any

from pydantic import ValidationError

from core.config import ProjectConfig
from core.models.story import SocialMetadata, Story, StoryScene
from core.prompts.story import STORY_SYSTEM_PROMPT, STORY_USER_PROMPT
from core.providers.base import StoryProvider


class GeminiStoryProvider(StoryProvider):
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.types = None
        self.genai = None
        try:
            from google import genai
            from google.genai import types

            self.genai = genai
            self.types = types
        except Exception as exc:
            self.logger.warning("google-genai is unavailable. Using fallback story: %s", exc)

    def generate_story(self, monster: str | None = None) -> Story:
        monster = monster or random.choice(self.config.story.monsters)
        api_keys = self.config.gemini_api_keys
        if not self.genai or not api_keys:
            self.logger.warning("GEMINI_API_KEY is missing. Using local fallback story.")
            return self._fallback_story(monster)

        prompt = STORY_USER_PROMPT.format(
            monster=monster,
            scene_count=self.config.story.scene_count,
        )
        last_error: Exception | None = None
        for key_index, api_key in enumerate(api_keys, start=1):
            try:
                client = self.genai.Client(api_key=api_key)
            except Exception as exc:
                last_error = exc
                self.logger.warning("Gemini client init failed for key %s: %s", key_index, exc)
                continue

            for attempt in range(1, self.config.gemini.max_retries + 1):
                try:
                    response = client.models.generate_content(
                        model=self.config.gemini.model,
                        contents=prompt,
                        config=self.types.GenerateContentConfig(
                            system_instruction=STORY_SYSTEM_PROMPT,
                            temperature=self.config.gemini.temperature,
                            response_mime_type="application/json",
                        ),
                    )
                    payload = self._json_from_text(response.text or "")
                    return self._coerce_story(payload, monster)
                except Exception as exc:
                    last_error = exc
                    self.logger.warning(
                        "Gemini key %s attempt %s failed: %s",
                        key_index,
                        attempt,
                        exc,
                    )
                    time.sleep(1.5 * attempt)

        self.logger.error("Gemini failed after retries: %s", last_error)
        return self._fallback_story(monster)

    def _json_from_text(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise
            return json.loads(text[start : end + 1])

    def _coerce_story(self, payload: dict[str, Any], monster: str) -> Story:
        payload.setdefault("monster", monster)
        payload.setdefault("title", f"La leyenda de {monster}")
        payload.setdefault("hook", "Nunca respondas si el bosque dice tu nombre.")
        payload["ending_question"] = self._normalize_ending_question(
            str(payload.get("ending_question") or ""),
            monster,
        )
        payload.setdefault("social", {})
        payload["social"] = self._social_defaults(payload["social"], payload["title"])

        scenes = payload.get("scenes") or []
        fixed_scenes = []
        for index, scene in enumerate(scenes[: self.config.story.scene_count], start=1):
            fixed_scenes.append(
                {
                    "index": index,
                    "text": str(scene.get("text") or scene.get("text_es") or "").strip(),
                    "image_prompt": str(scene.get("image_prompt") or "").strip(),
                }
            )
        payload["scenes"] = [scene for scene in fixed_scenes if scene["text"]]

        try:
            story = Story.model_validate(payload)
        except ValidationError as exc:
            self.logger.warning("Gemini story validation failed: %s", exc)
            return self._fallback_story(monster)

        if len(story.scenes) < 4:
            return self._fallback_story(monster)
        return story

    def _normalize_ending_question(self, text: str, monster: str) -> str:
        candidate = text.strip()
        if candidate.endswith("?"):
            return candidate
        return self._viral_question(monster)

    def _viral_question(self, monster: str) -> str:
        templates = [
            "¿Abrirías la puerta si llama con tu voz?",
            "¿Responderías si el bosque dijera tu nombre?",
            "¿Entrarías aunque oyeras llorar detrás?",
            "¿Mirarías atrás si alguien respirara tu nombre?",
        ]
        digest = hashlib.sha256(monster.encode("utf-8")).digest()
        return templates[digest[0] % len(templates)]

    def _social_defaults(self, social: dict[str, Any], title: str) -> dict[str, Any]:
        return {
            "youtube_title": social.get("youtube_title") or title[:58],
            "youtube_description": social.get("youtube_description")
            or f"{title}\n\n¿Te atreverías a entrar? Comenta tu respuesta.",
            "instagram_caption": social.get("instagram_caption")
            or f"{title}. ¿Qué harías tú?",
            "tiktok_caption": social.get("tiktok_caption")
            or f"{title}. ¿Mirarías atrás?",
            "hashtags": social.get("hashtags")
            or ["#terror", "#leyendas", "#horror", "#slavic", "#shorts", "#reels", "#tiktok"],
        }

    def _fallback_story(self, monster: str) -> Story:
        scenes = [
            ("Tu linterna parpadea junto al pozo abandonado.", "abandoned slavic village well at night, flashlight flickering"),
            ("Alguien respira debajo del hielo negro.", "black frozen river, breath under ice, horror"),
            ("Las ramas forman una puerta detrás de ti.", "twisted forest branches forming a doorway, dark folklore"),
            ("Una anciana canta con tu propia voz.", "old slavic woman in fog singing, unsettling face"),
            (f"Entonces {monster} aparece entre los troncos.", f"{monster} emerging from ancient trees, terrifying folklore creature"),
            ("Tus pasos vuelven, pero tú no caminas.", "muddy path with impossible footprints, night forest"),
            ("La casa enciende una vela por dentro.", "wooden hut in dark forest with one candle in window"),
            ("Y la puerta se abre sin manos.", "old wooden door opening by itself, cinematic horror"),
        ]
        social = SocialMetadata(
            youtube_title=f"Nunca sigas a {monster} en el bosque",
            youtube_description=(
                f"Una leyenda eslava sobre {monster}, un bosque que escucha y una puerta que no debería abrirse.\n\n"
                "¿Entrarías si escuchas tu nombre?"
            ),
            instagram_caption=f"El bosque sabe tu nombre. ¿Responderías? #terror",
            tiktok_caption=f"Si {monster} te llama, no mires atrás. ¿Lo harías?",
            hashtags=["#terror", "#horror", "#leyendas", "#mitologiaeslava", "#slavic", "#shorts", "#reels", "#tiktok"],
        )
        return Story(
            title=f"La puerta de {monster}",
            monster=monster,
            hook="Nunca respondas si el bosque dice tu nombre.",
            scenes=[
                StoryScene(index=i, text=text, image_prompt=f"{prompt}, vertical 9:16, no text")
                for i, (text, prompt) in enumerate(scenes[: self.config.story.scene_count], start=1)
            ],
            ending_question="¿Abrirías la puerta si llama con tu voz?",
            social=social,
        )
