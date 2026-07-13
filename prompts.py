"""
prompts.py
Slavic Horror Engine v2
"""

from monsters_database import get_monster_info, get_rotated_legends
import json
import os

CYCLE_TRACKER_FILE = "cycle_tracker.json"

def load_cycle_tracker():
    """Load cycle tracker from file."""
    if os.path.exists(CYCLE_TRACKER_FILE):
        try:
            with open(CYCLE_TRACKER_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"current_cycle": 0, "current_monster_index": 0}

def save_cycle_tracker(tracker):
    """Save cycle tracker to file."""
    with open(CYCLE_TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def get_current_monster(monsters_list):
    """Get current monster from list based on tracker."""
    tracker = load_cycle_tracker()
    
    if tracker["current_monster_index"] >= len(monsters_list):
        # Start new cycle
        tracker["current_cycle"] += 1
        tracker["current_monster_index"] = 0
        save_cycle_tracker(tracker)
    
    monster_name = monsters_list[tracker["current_monster_index"]]
    
    # Move to next monster for next time
    tracker["current_monster_index"] += 1
    save_cycle_tracker(tracker)
    
    return monster_name, tracker["current_cycle"]

SYSTEM_PROMPT = """
Ты профессиональный сценарист вирусных коротких хоррор-видео.

Пишешь только на испанском языке.

Твоя задача —
максимальное удержание аудитории.

 история должна быть похожа на настоящий случай.

Не объясняй.

Не морализируй.

Не используй длинные предложения.

Каждая фраза должна вызывать желание досмотреть дальше.
"""

def get_story_prompt(monster_name, cycle_number=0):
    """Generate story prompt with monster-specific lore."""
    monster_info = get_monster_info(monster_name)
    
    # Get rotated legends based on cycle number
    legends = get_rotated_legends(monster_name, cycle_number)
    legends_text = "\n".join([f"- {legend}" for legend in legends])
    
    behavior_text = monster_info["behavior"]
    description_text = monster_info["description"]
    
    return f"""
Создай вирусную историю для Shorts/TikTok/Reels.

Тема (монстр из славянской мифологии):
{monster_name}

Описание монстра:
{description_text}

Поведение:
{behavior_text}

Известные легенды (используй как вдохновение):
{legends_text}

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
• ИСПОЛЬЗУЙ легенды выше как основу для сюжета
• История должна ощущаться как реальная городская легенда

Важно: Создай ОРИГИНАЛЬНУЮ историю на основе этих легенд, не просто пересказывай их.
"""

STORY_PROMPT = get_story_prompt  # Function that takes monster_name and cycle_number

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

atmospheric horror

night scene

moonlight

shadows

mysterious

ancient slavic setting

folk horror

dark fantasy
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

Используй любопытство и страх.

Без кликбейта.

Используй слова: leyenda, terror, bosque, criatura.

История:

{story}
"""

YOUTUBE_DESCRIPTION_PROMPT = """
Создай SEO описание YouTube.

Язык:

испанский.

Структура:
1. Краткое описание истории (2-3 предложения)
2. Призыв к комментарию
3. Ключевые слова: leyendas eslavas, terror, folklore, criaturas mitológicas, bosque, misterio

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