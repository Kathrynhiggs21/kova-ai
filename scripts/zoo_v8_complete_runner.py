#!/usr/bin/env python3
"""Run the complete V8 pipeline with utility-card composition support."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from PIL import Image, ImageDraw, ImageFont, ImageOps

import zoo_v8_pipeline as pipeline

ORIGINAL_COMPOSE_CARD = pipeline.compose_card


def compose_card(row: Mapping[str, str], art_path: Path, out_path: Path) -> None:
    card_type = pipeline.clean(row.get("Type")).lower()
    if "utility" not in card_type:
        ORIGINAL_COMPOSE_CARD(row, art_path, out_path)
        return

    with Image.open(art_path) as source:
        image = ImageOps.fit(source.convert("RGB"), pipeline.MASTER_SIZE, method=Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    accent = pipeline.color_from_text(pipeline.clean(row.get("Pop Color")), pipeline.clean(row.get("Card ID")))
    panel = pipeline.material_color(pipeline.clean(row.get("Title Material")), accent)
    text_color = (245, 239, 222) if pipeline.luminance(panel) < 135 else (42, 35, 28)
    shadow_color = (20, 16, 13) if pipeline.luminance(panel) < 135 else (245, 232, 205)
    width, height = pipeline.MASTER_SIZE

    title = pipeline.clean(row.get("Subject")).upper()
    title_font = pipeline.fit_font(draw, title, width - 760, 150, 58, bold=True)
    pipeline.draw_centered(draw, (240, 165, width - 440, 535), title, title_font, text_color, shadow_color, 5)
    pipeline.draw_category_icon(draw, width - 420, 245, 150, pipeline.clean(row.get("Category")), text_color)

    category_label = pipeline.clean(row.get("Category")).upper()
    category_font = pipeline.fit_font(draw, category_label, width - 700, 70, 38, bold=True)
    pipeline.draw_centered(
        draw,
        (350, height - 900, width - 350, height - 760),
        category_label,
        category_font,
        text_color,
        shadow_color,
        2,
    )

    fact_font = ImageFont.truetype(pipeline.font_path(False, False), 48)
    lines = pipeline.wrap_text(draw, pipeline.clean(row.get("Fun Fact")), fact_font, width - 650, 6)
    y = height - 700
    for line in lines:
        draw.text((325, y), line, font=fact_font, fill=text_color, stroke_fill=shadow_color, stroke_width=1)
        y += 64

    card_id = pipeline.clean(row.get("Card ID"))
    id_font = pipeline.fit_font(draw, card_id, 350, 70, 42, bold=True)
    pipeline.draw_centered(
        draw,
        (width - 650, height - 430, width - 240, height - 215),
        card_id,
        id_font,
        text_color,
        shadow_color,
        3,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG", optimize=True)


def main() -> int:
    pipeline.compose_card = compose_card
    return pipeline.main()


if __name__ == "__main__":
    raise SystemExit(main())
