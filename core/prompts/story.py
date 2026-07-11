STORY_SYSTEM_PROMPT = """
You are a professional short-form horror writer.
Write only in Spanish.
The story must feel like a true incident from a Slavic village or forest.
Use short, sharp sentences with strong retention.
Return valid JSON only.
"""

STORY_USER_PROMPT = """
Create one vertical Shorts/TikTok/Reels horror script.

Monster: {monster}
Language: Spanish
Scene count: {scene_count}

Rules:
- The first line is a brutal hook.
- Every scene has 5-12 words.
- Use second person when possible.
- Escalate fear every scene.
- ÚLTIMA ESCENA — PREGUNTA VIRAL.
- The final line must be a direct question to the viewer.
- Do not end with a statement.
- Image prompts must be in English, photorealistic, vertical 9:16, no text, no watermark.

Return this exact JSON shape:
{{
  "title": "Spanish title",
  "monster": "{monster}",
  "hook": "Spanish hook",
  "scenes": [
    {{"index": 1, "text": "Spanish scene text", "image_prompt": "English image prompt"}},
    {{"index": 2, "text": "Spanish scene text", "image_prompt": "English image prompt"}}
  ],
  "ending_question": "Spanish question",
  "social": {{
    "youtube_title": "Clickable Spanish title under 60 chars",
    "youtube_description": "Spanish YouTube description with CTA",
    "instagram_caption": "Spanish Instagram caption with a question",
    "tiktok_caption": "Spanish TikTok caption under 180 chars",
    "hashtags": ["#terror", "#leyendas", "#shorts"]
  }}
}}
"""

IMAGE_STYLE_SUFFIX = """
photorealistic slavic horror movie still, vertical 9:16, 35mm lens,
cinematic lighting, volumetric fog, cold forest atmosphere, natural skin,
high detail, no text, no logo, no watermark
"""
