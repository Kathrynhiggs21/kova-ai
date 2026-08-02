#!/usr/bin/env python3
"""End-to-end Zoo V8 image pipeline.

Stages: source join -> data gate -> art plate (mock or Gemini) -> deterministic
composition -> app/thumbnail exports -> QA -> contact sheet -> manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import math
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from PIL import Image, ImageDraw, ImageFont, ImageOps

from zoo_v8_rules import augment_prompt

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "renders" / "v8"
REPORT_DIR = BASE_DIR / "reports" / "v8"
MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
API_KEY = os.getenv("GEMINI_API_KEY", "")
MASTER_SIZE = (2250, 3150)
APP_SIZE = (1000, 1400)
THUMB_SIZE = (360, 504)
BAD_VALUES = {"", "unknown", "research required", "n/a", "na", "none", "tbd"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CLASS_BY_CATEGORY = {
    "Mammals": "Mammal",
    "Birds of Prey & Waterfowl": "Bird",
    "Tropical & Songbirds": "Bird",
    "Reptiles & Amphibians": "Reptile / Amphibian",
    "Fish & Invertebrates": "Fish / Invertebrate",
    "Wildflowers": "Plant",
    "Trees": "Plant",
    "Herbs & Shrubs": "Plant",
    "Aquatic Plants": "Plant",
    "Vines & Climbing Plants": "Plant",
    "Insects & Arachnids": "Insect / Arachnid",
}


@dataclass
class AssetRecord:
    card_id: str
    category: str
    card_type: str
    subject: str
    data_status: str
    generation_mode: str
    model: str
    prompt_sha256: str
    art_plate: str
    master_png: str
    app_webp: str
    thumbnail_webp: str
    width: int
    height: int
    qa_status: str
    sha256: str
    category_back_id: str
    rules: dict


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing(value: object) -> bool:
    text = clean(value).lower()
    return text in BAD_VALUES or text.startswith("research required")


def safe_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", value)).strip("_")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Required source file is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"Source file has no rows: {path}")
    return rows


def normalize_lifespan(value: str) -> str:
    value = clean(value).replace("–", "-")
    if is_missing(value):
        return value
    return value if value.lower().startswith("lives ") else f"Lives {value}"


def category_back_for(category: str, inventory_rows: Iterable[Mapping[str, str]]) -> str:
    for row in inventory_rows:
        if clean(row.get("Type")).lower() == "card back" and clean(row.get("Category")) == clean(category):
            return clean(row.get("Card ID"))
    return ""


def data_status(row: Mapping[str, str]) -> str:
    card_type = clean(row.get("Type")).lower()
    if card_type == "card back":
        required = ("Card ID", "Category", "Subject", "Pop Color", "Background")
    elif "utility" in card_type:
        required = ("Card ID", "Category", "Subject", "Fun Fact", "Pop Color", "Title Material", "Background")
    else:
        required = (
            "Card ID", "Category", "Subject", "Scientific Name", "Lifespan", "Region",
            "Class", "Status", "Fun Fact", "Pop Color", "Title Material", "Background",
        )
    missing = [key for key in required if is_missing(row.get(key))]
    return "READY" if not missing else "BLOCKED: " + ", ".join(missing)


def resolve_identifier(row: Mapping[str, str]) -> str:
    subject = clean(row.get("Subject")).lower()
    category = clean(row.get("Category")).lower()
    if any(x in subject for x in ("monkey", "gibbon", "sifaka", "loris", "saki", "tamarin", "galago", "aye-aye", "potto", "siamang")):
        return "hand-like primate track"
    if any(x in subject for x in ("fox", "wolf", "dog", "coyote", "jackal")):
        return "narrow four-toe canid track"
    if any(x in subject for x in ("tiger", "lion", "cat", "leopard", "jaguar", "lynx", "bobcat")):
        return "round four-toe feline track"
    if any(x in subject for x in ("deer", "antelope", "giraffe", "goat", "sheep", "bison", "cow")):
        return "species-appropriate hoof track"
    if "bird" in category:
        return "species-appropriate three-toe bird track"
    if "reptile" in category or "amphibian" in category:
        return "species-appropriate foot or scale trace"
    if "insect" in category or "arachnid" in category:
        return "simplified species silhouette"
    if any(x in category for x in ("wildflower", "trees", "plants", "herbs", "vines")):
        return "leaf or seed silhouette"
    return clean(row.get("Identifier Sketch")) or "thematic line-art identifier"


def merge_sources(inventory_rows: list[dict[str, str]], species_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    species = {clean(row.get("Card_ID")).upper(): row for row in species_rows if clean(row.get("Card_ID"))}
    merged: list[dict[str, str]] = []
    for source in inventory_rows:
        row = dict(source)
        card_id = clean(row.get("Card ID")).upper()
        override = species.get(card_id)
        if override:
            mapping = {
                "Subject": "Common_Name",
                "Scientific Name": "Scientific_Name",
                "Lifespan": "Lifespan",
                "Region": "Region",
                "Status": "Conservation_Status",
                "Background": "Habitat_Background",
                "Fun Fact": "Fun_Fact",
                "Pop Color": "Pop_Color",
                "Title Material": "Title_Material",
                "Nature Density": "Nature_Density",
            }
            for target, src in mapping.items():
                value = clean(override.get(src))
                if value and not is_missing(value):
                    row[target] = value
            row["Lifespan"] = normalize_lifespan(row.get("Lifespan", ""))
            row["Data Source"] = "MASTER_SPECIES_DATABASE.csv + canonical inventory"
        else:
            row["Data Source"] = "canonical inventory"
        if is_missing(row.get("Class")) and row.get("Category") in CLASS_BY_CATEGORY:
            row["Class"] = CLASS_BY_CATEGORY[row["Category"]]
        row["Card ID"] = card_id
        row["Category Back ID"] = category_back_for(row.get("Category", ""), inventory_rows)
        row["Data Status"] = data_status(row)
        row["Identifier Resolved"] = resolve_identifier(row)
        merged.append(row)
    ids = [row["Card ID"] for row in merged]
    duplicates = sorted({card_id for card_id in ids if ids.count(card_id) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate canonical IDs: {duplicates[:10]}")
    return merged


def write_joined_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def select_rows(rows: list[dict[str, str]], card_ids: str, offset: int, limit: int) -> list[dict[str, str]]:
    if card_ids.strip():
        wanted = [value.strip().upper() for value in card_ids.split(",") if value.strip()]
        index = {row["Card ID"]: row for row in rows}
        missing = [value for value in wanted if value not in index]
        if missing:
            raise SystemExit(f"Unknown card IDs: {', '.join(missing)}")
        chosen = [index[value] for value in wanted]
    else:
        chosen = rows[offset:]
        if limit > 0:
            chosen = chosen[:limit]
    if not chosen:
        raise SystemExit("No cards selected")
    return chosen


def build_base_prompt(row: Mapping[str, str]) -> str:
    if clean(row.get("Type")).lower() == "card back":
        return f"""Create a premium category-back art plate for the Zoo Adventure collection.
Category: {clean(row.get('Category'))}
Hero motif: {clean(row.get('Subject'))}
Palette: {clean(row.get('Pop Color'))}
Atmosphere: {clean(row.get('Background'))}
Use a centered emblematic subject, layered painterly natural texture, and a clean blank central title-safe area. No lettering, numbers, logos, footer, or fake text."""
    return f"""Create a premium realistic natural-history collectible card art plate.
Exact subject: {clean(row.get('Subject'))}
Scientific identity for anatomy only: {clean(row.get('Scientific Name'))}
Habitat: {clean(row.get('Background'))}
Outer accent family: {clean(row.get('Pop Color'))}
Panel/frame material: {clean(row.get('Title Material'))}
Nature density: {clean(row.get('Nature Density'))}
The subject is large, sharp, calm, accurate, and visually dominant. The habitat has realistic depth. Use asymmetrical habitat framing and blank physical title/lower-panel surfaces. No lettering, numbers, icons, logos, footer branding, or fake glyphs."""


def color_from_text(text: str, card_id: str) -> tuple[int, int, int]:
    lowered = text.lower()
    named = [
        (("black", "charcoal", "midnight", "navy"), (40, 49, 66)),
        (("white", "silver"), (188, 193, 187)),
        (("yellow", "gold", "amber", "ochre"), (212, 154, 56)),
        (("orange", "apricot", "rust"), (203, 104, 48)),
        (("red", "burgundy", "berry"), (132, 54, 55)),
        (("green", "sage", "emerald", "forest", "moss"), (66, 113, 76)),
        (("blue", "teal", "ocean", "sky"), (52, 111, 132)),
        (("purple", "violet"), (103, 74, 123)),
        (("brown", "tan", "sand", "sandy", "buff"), (170, 130, 81)),
    ]
    for words, rgb in named:
        if any(word in lowered for word in words):
            return rgb
    digest = hashlib.sha256((card_id + text).encode()).digest()
    return (70 + digest[0] % 120, 70 + digest[1] % 120, 70 + digest[2] % 120)


def lighten(color, amount: float):
    return tuple(round(value + (255 - value) * amount) for value in color)


def darken(color, amount: float):
    return tuple(round(value * (1 - amount)) for value in color)


def material_color(material: str, accent: tuple[int, int, int]) -> tuple[int, int, int]:
    lowered = material.lower()
    if any(value in lowered for value in ("dark", "ebony", "mahogany", "charcoal")):
        return (64, 45, 33)
    if any(value in lowered for value in ("sandstone", "sun-bleached", "light", "pale")):
        return (205, 176, 132)
    if "metal" in lowered:
        return (102, 105, 101)
    if "stone" in lowered:
        return (113, 105, 91)
    return darken(accent, 0.48)


def font_path(bold: bool = False, italic: bool = False) -> str:
    if bold and italic:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"]
    elif bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        ]
    elif italic:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
        ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return "DejaVuSerif.ttf"


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    size = start
    while size >= minimum:
        font = ImageFont.truetype(font_path(bold, italic), size)
        if draw.textbbox((0, 0), text, font=font, stroke_width=max(1, size // 40))[2] <= max_width:
            return font
        size -= 4
    return ImageFont.truetype(font_path(bold, italic), minimum)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + "…", font=font)[2] > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def mock_art_plate(row: Mapping[str, str], out_path: Path) -> None:
    width, height = MASTER_SIZE
    accent = color_from_text(clean(row.get("Pop Color")), clean(row.get("Card ID")))
    dark = darken(accent, 0.55)
    light = lighten(accent, 0.55)
    gradient = Image.linear_gradient("L").resize((width, height))
    image = ImageOps.colorize(gradient, dark, light).convert("RGB")
    noise = Image.effect_noise((width, height), 12).convert("L")
    noise_rgb = ImageOps.colorize(noise, (224, 224, 224), (255, 255, 255))
    image = Image.blend(image, noise_rgb, 0.08)
    rng = random.Random(int(hashlib.sha256(clean(row.get("Card ID")).encode()).hexdigest()[:10], 16))
    draw = ImageDraw.Draw(image, "RGBA")
    frame = material_color(clean(row.get("Title Material")), accent)
    for _ in range(18):
        side = rng.choice(("left", "right", "top", "bottom"))
        if side == "left":
            x0, x1 = -120, rng.randint(120, 360)
            y0 = rng.randint(0, height - 280)
            y1 = min(height + 80, y0 + rng.randint(220, 900))
        elif side == "right":
            x0, x1 = rng.randint(width - 350, width - 80), width + 100
            y0 = rng.randint(0, height - 280)
            y1 = min(height + 80, y0 + rng.randint(220, 900))
        elif side == "top":
            x0 = rng.randint(0, width - 300)
            x1 = min(width + 80, x0 + rng.randint(260, 900))
            y0, y1 = -80, rng.randint(130, 400)
        else:
            x0 = rng.randint(0, width - 300)
            x1 = min(width + 80, x0 + rng.randint(260, 900))
            y0, y1 = rng.randint(height - 420, height - 100), height + 80
        draw.ellipse((x0, y0, x1, y1), fill=(*darken(frame, rng.random() * 0.2), rng.randint(130, 210)))
    draw.rounded_rectangle((180, 330, width - 180, height - 620), radius=100, fill=(*darken(accent, 0.25), 180))
    if clean(row.get("Type")).lower() == "card back":
        draw.ellipse((560, 750, 1690, 1900), fill=(*lighten(accent, 0.2), 230), outline=(*darken(accent, 0.4), 255), width=32)
    else:
        draw.ellipse((690, 650, 1580, 1870), fill=(220, 210, 190, 235), outline=(65, 55, 45, 255), width=30)
        draw.ellipse((820, 520, 1450, 1120), fill=(220, 210, 190, 235), outline=(65, 55, 45, 255), width=30)
    panel = material_color(clean(row.get("Title Material")), accent)
    draw.rounded_rectangle((210, 145, width - 210, 555), radius=55, fill=(*panel, 245), outline=(*lighten(panel, 0.2), 255), width=20)
    draw.rounded_rectangle((170, height - 930, width - 170, height - 145), radius=70, fill=(*panel, 245), outline=(*lighten(panel, 0.2), 255), width=20)
    draw.rounded_rectangle((width - 660, height - 440, width - 235, height - 205), radius=45, fill=(*lighten(panel, 0.08), 255), outline=(*darken(panel, 0.3), 255), width=16)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG", optimize=True)


def gemini_art_plate(prompt: str, image_size: str, out_path: Path, retries: int = 2) -> None:
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=API_KEY)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    response_format={"image": {"aspect_ratio": "3:4", "image_size": image_size}},
                ),
            )
            generated = None
            for part in response.parts or []:
                if getattr(part, "inline_data", None):
                    generated = part.as_image()
                    break
            if generated is None:
                raise RuntimeError("Gemini response contained no image")
            buffer = io.BytesIO()
            generated.save(buffer, format="PNG")
            with Image.open(io.BytesIO(buffer.getvalue())) as source:
                source = source.convert("RGB")
                width, height = source.size
                target_ratio = 5 / 7
                if width / height > target_ratio:
                    new_width = round(height * target_ratio)
                    left = (width - new_width) // 2
                    source = source.crop((left, 0, left + new_width, height))
                else:
                    new_height = round(width / target_ratio)
                    top = (height - new_height) // 2
                    source = source.crop((0, top, width, top + new_height))
                source = source.resize(MASTER_SIZE, Image.Resampling.LANCZOS)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                source.save(out_path, "PNG", optimize=True)
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt + random.random())
    raise RuntimeError(f"Gemini generation failed after retries: {last_error}")


def luminance(rgb: tuple[int, int, int]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def draw_centered(draw, box, text, font, fill, stroke_fill, stroke_width=2):
    x0, y0, x1, y1 = box
    bounds = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = x0 + (x1 - x0 - (bounds[2] - bounds[0])) / 2
    y = y0 + (y1 - y0 - (bounds[3] - bounds[1])) / 2 - bounds[1]
    draw.text((x, y), text, font=font, fill=fill, stroke_fill=stroke_fill, stroke_width=stroke_width)


def draw_category_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, category: str, fill):
    lowered = category.lower()
    s = size
    if "mammal" in lowered:
        draw.ellipse((x + s * 0.28, y + s * 0.42, x + s * 0.72, y + s * 0.9), fill=fill)
        for dx, dy in ((0.12, 0.18), (0.34, 0.05), (0.58, 0.05), (0.8, 0.18)):
            draw.ellipse((x + s * dx, y + s * dy, x + s * (dx + 0.18), y + s * (dy + 0.2)), fill=fill)
    elif "bird" in lowered:
        draw.arc((x, y, x + s, y + s), 20, 320, fill=fill, width=max(3, s // 12))
        draw.line((x + s * 0.25, y + s * 0.7, x + s * 0.82, y + s * 0.2), fill=fill, width=max(3, s // 14))
    elif "fish" in lowered or "aquatic" in lowered:
        draw.ellipse((x + s * 0.1, y + s * 0.25, x + s * 0.75, y + s * 0.75), outline=fill, width=max(3, s // 14))
        draw.polygon([(x + s * 0.7, y + s * 0.5), (x + s, y + s * 0.18), (x + s, y + s * 0.82)], fill=fill)
    elif any(key in lowered for key in ("plant", "flower", "trees", "herbs", "vines", "garden")):
        draw.ellipse((x + s * 0.2, y + s * 0.05, x + s * 0.75, y + s * 0.65), fill=fill)
        draw.line((x + s * 0.48, y + s * 0.55, x + s * 0.45, y + s), fill=fill, width=max(3, s // 14))
    elif "insect" in lowered or "arachnid" in lowered:
        draw.ellipse((x + s * 0.35, y + s * 0.2, x + s * 0.65, y + s * 0.85), fill=fill)
        draw.ellipse((x, y + s * 0.15, x + s * 0.45, y + s * 0.6), outline=fill, width=max(3, s // 16))
        draw.ellipse((x + s * 0.55, y + s * 0.15, x + s, y + s * 0.6), outline=fill, width=max(3, s // 16))
    else:
        draw.regular_polygon((x + s / 2, y + s / 2, s * 0.42), 5, fill=fill)


def draw_identifier(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, descriptor: str, fill):
    lowered = descriptor.lower()
    if "hoof" in lowered:
        draw.ellipse((x, y, x + size * 0.45, y + size), outline=fill, width=10)
        draw.ellipse((x + size * 0.48, y, x + size * 0.93, y + size), outline=fill, width=10)
    elif "bird" in lowered:
        draw.line((x + size * 0.5, y + size * 0.15, x + size * 0.5, y + size * 0.75), fill=fill, width=10)
        for angle in (-0.5, 0, 0.5):
            draw.line((x + size * 0.5, y + size * 0.7, x + size * (0.5 + angle), y + size), fill=fill, width=8)
    elif "hand" in lowered or "primate" in lowered:
        draw.ellipse((x + size * 0.25, y + size * 0.45, x + size * 0.75, y + size * 0.95), outline=fill, width=10)
        for index in range(5):
            xx = x + size * (0.12 + index * 0.19)
            draw.line((xx, y + size * 0.55, xx + size * 0.05, y + size * (0.05 if index == 2 else 0.2)), fill=fill, width=8)
    else:
        draw.ellipse((x + size * 0.2, y + size * 0.42, x + size * 0.8, y + size), outline=fill, width=10)
        for index in range(4):
            xx = x + size * (0.08 + index * 0.23)
            draw.ellipse((xx, y + size * 0.05, xx + size * 0.2, y + size * 0.35), outline=fill, width=8)


def compose_card(row: Mapping[str, str], art_path: Path, out_path: Path) -> None:
    with Image.open(art_path) as source:
        image = ImageOps.fit(source.convert("RGB"), MASTER_SIZE, method=Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    accent = color_from_text(clean(row.get("Pop Color")), clean(row.get("Card ID")))
    panel = material_color(clean(row.get("Title Material")), accent)
    text_color = (245, 239, 222) if luminance(panel) < 135 else (42, 35, 28)
    shadow_color = (20, 16, 13) if luminance(panel) < 135 else (245, 232, 205)
    width, height = MASTER_SIZE
    card_type = clean(row.get("Type")).lower()
    if card_type == "card back":
        title = clean(row.get("Category")).upper()
        title_font = fit_font(draw, title, width - 430, 150, 70, bold=True)
        draw_centered(draw, (210, 170, width - 210, 550), title, title_font, text_color, shadow_color, 5)
        subject = clean(row.get("Subject"))
        subject_font = fit_font(draw, subject, width - 500, 84, 48, italic=True)
        draw_centered(draw, (250, height - 820, width - 250, height - 590), subject, subject_font, text_color, shadow_color, 3)
        brand = "MILLI MILES ZOO ADVENTURE"
        brand_font = fit_font(draw, brand, width - 520, 76, 42, bold=True)
        draw_centered(draw, (260, height - 580, width - 260, height - 390), brand, brand_font, text_color, shadow_color, 3)
        card_id = clean(row.get("Card ID"))
        card_font = fit_font(draw, card_id, 360, 68, 40, bold=True)
        draw_centered(draw, (width - 650, height - 430, width - 240, height - 215), card_id, card_font, text_color, shadow_color, 3)
    else:
        title = clean(row.get("Subject")).upper()
        title_font = fit_font(draw, title, width - 760, 150, 58, bold=True)
        draw_centered(draw, (240, 165, width - 440, 535), title, title_font, text_color, shadow_color, 5)
        draw_category_icon(draw, width - 420, 245, 150, clean(row.get("Category")), text_color)
        scientific = clean(row.get("Scientific Name")).strip("*")
        scientific_font = fit_font(draw, scientific, width - 720, 68, 42, italic=True)
        draw_centered(draw, (330, height - 900, width - 330, height - 770), scientific, scientific_font, text_color, shadow_color, 2)
        stats = " | ".join(
            value for value in (
                clean(row.get("Lifespan")), clean(row.get("Region")),
                clean(row.get("Class")), clean(row.get("Status")),
            ) if not is_missing(value)
        )
        stats_font = fit_font(draw, stats, width - 520, 48, 32, bold=True)
        draw_centered(draw, (260, height - 775, width - 260, height - 655), stats, stats_font, text_color, shadow_color, 1)
        fact_font = ImageFont.truetype(font_path(), 43)
        lines = wrap_text(draw, "Fun fact: " + clean(row.get("Fun Fact")), fact_font, width - 780, 4)
        y = height - 635
        for line in lines:
            draw.text((460, y), line, font=fact_font, fill=text_color, stroke_fill=shadow_color, stroke_width=1)
            y += 58
        draw_identifier(draw, 240, height - 585, 170, clean(row.get("Identifier Resolved")), text_color)
        card_id = clean(row.get("Card ID"))
        card_font = fit_font(draw, card_id, 350, 70, 42, bold=True)
        draw_centered(draw, (width - 650, height - 430, width - 240, height - 215), card_id, card_font, text_color, shadow_color, 3)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG", optimize=True)


def export_variants(master_path: Path, app_path: Path, thumb_path: Path) -> None:
    with Image.open(master_path) as image:
        rgb = image.convert("RGB")
        app = rgb.resize(APP_SIZE, Image.Resampling.LANCZOS)
        thumb = rgb.resize(THUMB_SIZE, Image.Resampling.LANCZOS)
        app_path.parent.mkdir(parents=True, exist_ok=True)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        app.save(app_path, "WEBP", quality=92, method=6)
        thumb.save(thumb_path, "WEBP", quality=86, method=6)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def qa_asset(master: Path, app: Path, thumb: Path, row: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    for path, size in ((master, MASTER_SIZE), (app, APP_SIZE), (thumb, THUMB_SIZE)):
        if not path.exists() or path.stat().st_size < 1000:
            errors.append(f"missing/small {path}")
            continue
        with Image.open(path) as image:
            if image.size != size:
                errors.append(f"{path.name} size {image.size}, expected {size}")
            if abs(image.width / image.height - 5 / 7) > 0.001:
                errors.append(f"{path.name} is not 5:7")
    if clean(row.get("Data Status")) != "READY":
        errors.append(clean(row.get("Data Status")))
    return errors


def contact_sheet(records: list[AssetRecord], path: Path) -> None:
    if not records:
        return
    columns = min(4, len(records))
    rows = math.ceil(len(records) / columns)
    tile = (360, 560)
    canvas = Image.new("RGB", (columns * tile[0], rows * tile[1]), (28, 28, 28))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_path(True), 25)
    for index, record in enumerate(records):
        with Image.open(BASE_DIR / record.thumbnail_webp) as image:
            x = (index % columns) * tile[0]
            y = (index // columns) * tile[1]
            canvas.paste(image.convert("RGB"), (x, y))
            full_label = f"{record.card_id}  {record.subject}"
            label = full_label
            while label and draw.textbbox((0, 0), label, font=font)[2] > tile[0] - 20:
                label = label[:-1]
            if label != full_label:
                label = label.rstrip() + "…"
            draw.text((x + 10, y + 510), label, font=font, fill=(240, 240, 240))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "JPEG", quality=90)


def process_one(row: dict[str, str], generation_mode: str, image_size: str, overwrite: bool) -> AssetRecord:
    card_id = row["Card ID"]
    slug = f"{safe_name(card_id)}_{safe_name(row.get('Subject', 'Card'))}"
    art_path = OUTPUT_DIR / "art_plates" / f"{slug}_V8_art_plate.png"
    master_path = OUTPUT_DIR / "masters" / f"{slug}_V8_master.png"
    app_path = OUTPUT_DIR / "app" / f"{slug}_V8.webp"
    thumb_path = OUTPUT_DIR / "thumbnails" / f"{slug}_V8_thumb.webp"
    base_prompt = build_base_prompt(row)
    prompt, rules = augment_prompt(row, base_prompt, "art-plate")
    if overwrite or not art_path.exists():
        if generation_mode == "mock":
            mock_art_plate(row, art_path)
        else:
            gemini_art_plate(prompt, image_size, art_path)
    compose_card(row, art_path, master_path)
    export_variants(master_path, app_path, thumb_path)
    problems = qa_asset(master_path, app_path, thumb_path, row)
    return AssetRecord(
        card_id=card_id,
        category=clean(row.get("Category")),
        card_type=clean(row.get("Type")),
        subject=clean(row.get("Subject")),
        data_status=clean(row.get("Data Status")),
        generation_mode=generation_mode,
        model=MODEL_NAME if generation_mode == "gemini" else "deterministic-mock-art-v1",
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        art_plate=str(art_path.relative_to(BASE_DIR)),
        master_png=str(master_path.relative_to(BASE_DIR)),
        app_webp=str(app_path.relative_to(BASE_DIR)),
        thumbnail_webp=str(thumb_path.relative_to(BASE_DIR)),
        width=MASTER_SIZE[0],
        height=MASTER_SIZE[1],
        qa_status="PASS" if not problems else "FAIL: " + "; ".join(problems),
        sha256=sha256_file(master_path),
        category_back_id=clean(row.get("Category Back ID")),
        rules=rules.to_dict(),
    )


def write_manifest(records: list[AssetRecord], path: Path) -> None:
    payload = {
        "version": "V8",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(records),
        "cards": [asdict(record) for record in records],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Complete Zoo V8 image-production pipeline")
    parser.add_argument("--inventory", type=Path, default=DATA_DIR / "MASTER_CARD_PRODUCTION_DATABASE.csv")
    parser.add_argument("--species", type=Path, default=DATA_DIR / "MASTER_SPECIES_DATABASE.csv")
    parser.add_argument("--generation-mode", choices=("mock", "gemini"), default="mock")
    parser.add_argument("--card-ids", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--image-size", choices=("1K", "2K", "4K"), default="2K")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--allow-blocked", action="store_true", help="Mock diagnostics only; paid Gemini mode never permits blocked data")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    inventory = read_csv(args.inventory)
    species = read_csv(args.species)
    rows = merge_sources(inventory, species)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_joined_csv(rows, REPORT_DIR / "zoo_v8_joined_data.csv")
    summary = {
        "total": len(rows),
        "ready": sum(row["Data Status"] == "READY" for row in rows),
        "blocked": sum(row["Data Status"] != "READY" for row in rows),
        "fronts": sum("front" in row["Type"].lower() for row in rows),
        "backs": sum(row["Type"].lower() == "card back" for row in rows),
    }
    (REPORT_DIR / "data_preflight_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    selected = select_rows(rows, args.card_ids, args.offset, args.limit)
    blocked = [row for row in selected if row["Data Status"] != "READY"]
    if blocked and (args.generation_mode == "gemini" or not args.allow_blocked):
        details = "\n".join(f"{row['Card ID']}: {row['Data Status']}" for row in blocked[:30])
        raise SystemExit(f"Data gate blocked {len(blocked)} selected card(s):\n{details}")
    if args.generation_mode == "gemini" and not API_KEY:
        raise SystemExit("GEMINI_API_KEY is missing")

    records: list[AssetRecord] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = {
            pool.submit(process_one, row, args.generation_mode, args.image_size, args.overwrite): row
            for row in selected
        }
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            logging.info("%s %s", record.card_id, record.qa_status)

    order = {row["Card ID"]: index for index, row in enumerate(selected)}
    records.sort(key=lambda record: order[record.card_id])
    write_manifest(records, REPORT_DIR / "cards-v8.json")
    contact_sheet(records, REPORT_DIR / "contact_sheet_v8.jpg")
    failed = [record for record in records if record.qa_status != "PASS"]
    run_summary = {
        **summary,
        "selected": len(selected),
        "generated": len(records),
        "qa_pass": len(records) - len(failed),
        "qa_fail": len(failed),
        "generation_mode": args.generation_mode,
        "model": MODEL_NAME if args.generation_mode == "gemini" else "deterministic-mock-art-v1",
    }
    (REPORT_DIR / "run_summary.json").write_text(json.dumps(run_summary, indent=2), encoding="utf-8")
    print(json.dumps(run_summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
