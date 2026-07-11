from __future__ import annotations

import re
import textwrap


def wrap_subtitle(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    lines: list[str] = []
    for part in textwrap.wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False):
        lines.append(part)
    return lines or [text]


def srt_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
