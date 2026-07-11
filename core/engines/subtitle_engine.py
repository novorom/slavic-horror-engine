from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.config import ProjectConfig
from core.utils.image import cover_resize
from core.utils.text import srt_timestamp, wrap_subtitle


class SubtitleEngine:
    def __init__(self, config: ProjectConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.subtitle_dir = config.paths.cache / "subtitles"
        self.subtitle_dir.mkdir(parents=True, exist_ok=True)

    def burn(self, image_path: Path, text: str, index: int) -> Path:
        image = Image.open(image_path).convert("RGBA")
        if image.size != self.config.video.size:
            image = cover_resize(image.convert("RGB"), self.config.video.size).convert("RGBA")
        width, height = image.size
        font = self._font()
        lines = wrap_subtitle(text.upper(), self.config.subtitles.max_chars_per_line)
        line_height = int(self.config.subtitles.font_size * 1.18)
        total_height = max(line_height * len(lines), line_height)
        y0 = height - self.config.subtitles.bottom_margin - total_height

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        max_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=self.config.subtitles.stroke_width)
            max_width = max(max_width, bbox[2] - bbox[0])
        box_padding_x = 34
        box_padding_y = 22
        box = (
            width // 2 - max_width // 2 - box_padding_x,
            y0 - box_padding_y,
            width // 2 + max_width // 2 + box_padding_x,
            y0 + total_height + box_padding_y,
        )
        draw.rounded_rectangle(box, radius=18, fill=(0, 0, 0, self.config.subtitles.box_opacity))
        image = Image.alpha_composite(image, overlay)

        draw = ImageDraw.Draw(image)
        for line_index, line in enumerate(lines):
            y = y0 + line_index * line_height + line_height // 2
            draw.text(
                (width // 2, y),
                line,
                font=font,
                anchor="mm",
                fill=self.config.subtitles.text_color,
                stroke_fill=self.config.subtitles.stroke_color,
                stroke_width=self.config.subtitles.stroke_width,
            )

        output = self.subtitle_dir / f"scene_{index:02}.jpg"
        image.convert("RGB").save(output, quality=95, optimize=True)
        return output

    def write_srt(self, lines: list[str], durations: list[float]) -> Path:
        output = self.config.paths.output / "subtitles.srt"
        cursor = 0.0
        blocks: list[str] = []
        for index, (line, duration) in enumerate(zip(lines, durations), start=1):
            start = cursor
            end = cursor + duration
            blocks.append(f"{index}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{line}\n")
            cursor = end
        output.write_text("\n".join(blocks), encoding="utf-8")
        return output

    def _font(self) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            self.config.subtitles.font_file,
            str(self.config.paths.fonts / "BebasNeue.ttf"),
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                try:
                    return ImageFont.truetype(candidate, self.config.subtitles.font_size)
                except Exception:
                    continue
        return ImageFont.load_default()
