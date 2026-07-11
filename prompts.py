"""
prompts.py
Slavic Horror Engine v2
"""

SYSTEM_PROMPT = """
Ты профессиональный сценарист вирусных коротких хоррор-видео.

Пишешь только на испанском языке.

Твоя задача —
максимальное удержание аудитории.

История должна быть похожа на настоящий случай.

Не объясняй.

Не морализируй.

Не используй длинные предложения.

Каждая фраза должна вызывать желание досмотреть дальше.
"""

STORY_PROMPT = """
Создай вирусную историю для Shorts/TikTok/Reels.

Тема:
{monster}

Формат:

HOOK
SCENE 1
SCENE 2
SCENE 3
SCENE 4
SCENE 5
SCENE 6
ENDING QUESTION

Правила:

• язык — испанский
• максимум 8 сцен
• каждая сцена 5–12 слов
• никакой воды
• никаких длинных описаний
• каждый новый кадр усиливает страх
• финал остается открытым
• последний кадр — вопрос зрителю

История должна ощущаться как реальная городская легенда.
"""

IMAGE_PROMPT = """
Ultra realistic horror movie still.

Scene:

{scene}

Monster:

{monster}

Requirements:

photorealistic

masterpiece

8k

cinematic

35mm lens

dramatic lighting

volumetric fog

ultra detailed

dark forest

cold atmosphere

slavic folklore

terrifying creature

high realism

Unreal Engine 5

real skin

professional photography

vertical composition

no text

no watermark

no logo
"""

THUMBNAIL_PROMPT = """
Ultra realistic horror close-up.

Most terrifying moment.

Eye contact.

Extreme cinematic lighting.

Masterpiece.

Dark background.

Photorealistic.

Vertical.

No text.

No logo.
"""

YOUTUBE_TITLE_PROMPT = """
Напиши 10 максимально кликабельных заголовков YouTube Shorts.

Язык:
испанский.

Максимум 60 символов.

Используй любопытство.

Без кликбейта.

История:

{story}
"""

YOUTUBE_DESCRIPTION_PROMPT = """
Создай SEO описание YouTube.

Язык:

испанский.

Добавь призыв к комментарию.

Добавь естественные ключевые слова.

История:

{story}
"""

TIKTOK_PROMPT = """
Создай подпись TikTok.

Максимум 180 символов.

Испанский.

Добавь вопрос.

История:

{story}
"""

INSTAGRAM_PROMPT = """
Создай описание Instagram Reels.

Испанский.

Добавь вопрос.

Добавь эмоции.

История:

{story}
"""

HASHTAGS_PROMPT = """
Создай 20 популярных испанских хэштегов.

Тематика:

horror

terror

leyendas

bosque

criaturas

folklore

slavic

shorts

reels

tiktok
"""

COMMENT_PROMPT = """
Создай комментарий, который автор закрепит.

Он должен провоцировать обсуждение.

Испанский.
"""

HOOK_EXAMPLES = [

"Nunca respondas si escuchas tu nombre en el bosque.",

"Si ves esto de noche... corre.",

"Mi abuelo me prohibió mirar atrás.",

"Nadie sobrevivió después de escuchar ese silbido.",

"Hay un bosque donde nunca amanece.",

"Lo que encontraron bajo el lago sigue vivo.",

"No aceptes comida de una anciana en el bosque.",

"Los niños del pueblo desaparecen cada invierno.",

"Jamás sigas una voz entre los árboles.",

"Dicen que todavía espera a la próxima víctima."

]

ENDING_QUESTIONS = [

"¿Entrarías allí?",

"¿Qué habrías hecho tú?",

"¿Te atreverías a mirar?",

"¿Crees que esta leyenda es real?",

"¿Escuchaste algo extraño?",

"¿Sobrevivirías una noche allí?",

"¿Volverías al bosque?",

"¿La llamarías por su nombre?",

"¿Abrirías esa puerta?",

"¿Qué harías en su lugar?"

]