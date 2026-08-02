from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Mapping

PROHIBITED_STYLE_TERMS = (
    "neon",
    "rainbow",
    "glowing border",
    "uniform border",
    "plastic rim",
    "chrome rim",
)

PALETTES = (
    {"id": "forest_rust", "keywords": ("forest", "bamboo", "woodland", "panda", "tiger", "fox", "mammal"), "family": "warm rust red, muted bamboo green, and amber-brown", "source": "fur, bark, and forest foliage"},
    {"id": "desert_apricot", "keywords": ("desert", "sand", "dune", "fennec", "arid", "savanna"), "family": "sunlit apricot, sand-gold, and warm ochre", "source": "sand, sunlit fur, and dry habitat tones"},
    {"id": "wetland_teal", "keywords": ("water", "river", "ocean", "reef", "fish", "aquatic", "wetland"), "family": "deep teal, mineral blue-green, and muted turquoise", "source": "water, scales, and aquatic vegetation"},
    {"id": "botanical_berry", "keywords": ("flower", "plant", "botanical", "orchid", "butterfly", "pollinator", "garden"), "family": "berry, petal coral, and leaf green", "source": "petals, wings, leaves, and botanical details"},
    {"id": "stone_moss", "keywords": ("stone", "rock", "mountain", "alpine", "reptile", "amphibian", "moss"), "family": "moss green, slate blue, and mineral amber", "source": "stone, moss, scales, and shaded habitat"},
    {"id": "sky_gold", "keywords": ("bird", "eagle", "raptor", "sky", "aviary", "feather"), "family": "sky blue, feather gold, and muted sunset copper", "source": "feathers, open sky, and sunlit habitat"},
    {"id": "archive_bronze", "keywords": ("history", "zoo", "archive", "map", "utility", "story"), "family": "archive green, aged bronze, and museum burgundy", "source": "historic signage, archival materials, and aged metal"},
)

DISTRIBUTIONS = (
    "strongest in two unequal corners with narrow side openings",
    "visible through irregular left-edge gaps and one opposite corner",
    "broken perimeter pockets behind branches, roots, or stone",
    "uneven corner exposure with small interruptions along both sides",
)
INTENSITIES = ("subtle but unmistakable", "medium and atmospheric", "rich but secondary")
PLAQUE_SHAPES = ("carved tab", "irregular inset plaque", "rounded organic plate", "small shield-like plaque")
PLAQUE_EDGES = ("hand-cut edge", "softly beveled edge", "weathered irregular edge", "fine carved edge")
PLAQUE_MOUNTS = ("integrated into the lower panel", "nested into the frame", "attached with restrained natural hardware")


def _text(row: Mapping[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value and str(value).strip():
            return str(value).strip()
    return ""


def _seed(card_id: str, label: str) -> int:
    digest = hashlib.sha256(f"{card_id}|{label}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _choose(card_id: str, label: str, options):
    return options[_seed(card_id, label) % len(options)]


def _parse_visibility(value: str, card_id: str) -> int:
    if value:
        match = re.search(r"(\d{1,2})", value)
        if match and 8 <= int(match.group(1)) <= 18:
            return int(match.group(1))
    return 8 + (_seed(card_id, "pop_visibility") % 11)


@dataclass(frozen=True)
class V8Rules:
    pop_color_family: str
    pop_color_source: str
    pop_color_visibility_target: int
    pop_color_intensity: str
    pop_color_distribution: str
    title_rule: str
    info_panel_rule: str
    shared_panel_material_rule: str
    text_contrast_rule: str
    plaque_material_rule: str
    plaque_shape: str
    plaque_edge: str
    plaque_mounting: str

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_v8_rules(row: Mapping[str, str]) -> V8Rules:
    card_id = _text(row, "Card ID", "Card_ID", "id")
    searchable = " ".join(
        _text(row, key)
        for key in ("Subject", "Species", "Habitat", "Background", "Category", "Class", "Prompt")
    ).lower()

    ranked = []
    for palette in PALETTES:
        ranked.append((sum(1 for word in palette["keywords"] if word in searchable), palette))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    palette = ranked[0][1] if ranked[0][0] else _choose(card_id, "palette", PALETTES)

    panel_material = _text(
        row,
        "Panel Material",
        "Title Material",
        "Frame Material",
        "Material Family",
    ) or "the card's habitat-matched organic material family"

    return V8Rules(
        pop_color_family=_text(row, "Pop Color Family", "Pop Color", "pop_color_family") or palette["family"],
        pop_color_source=_text(row, "Pop Color Source", "pop_color_source") or palette["source"],
        pop_color_visibility_target=_parse_visibility(
            _text(row, "Pop Color Visibility", "pop_color_visibility_target"), card_id
        ),
        pop_color_intensity=_text(row, "Pop Color Intensity", "pop_color_intensity")
        or _choose(card_id, "intensity", INTENSITIES),
        pop_color_distribution=_text(row, "Pop Color Distribution", "pop_color_distribution")
        or _choose(card_id, "distribution", DISTRIBUTIONS),
        title_rule=(
            "ALL CAPS; Red Panda-derived carved serif profile, larger cap forms, dimensional shadowing, "
            "retained natural intricacy, and restrained hand-carved irregularity"
        ),
        info_panel_rule=(
            "Fennec Fox lower-panel hierarchy: scientific name, compact stat line, fun fact, identifier at lower left, "
            "canonical number plaque at lower right"
        ),
        shared_panel_material_rule=(
            f"Use the exact same continuous organic material, species, color, grain, texture, age, finish, and edge language for both "
            f"the top title box and lower information box: {panel_material}. They may differ in shape and size, but must read as "
            "two pieces cut from the same physical source material. Never mix wood with parchment, bark with stone, or dark and light panel materials on one card"
        ),
        text_contrast_rule=(
            "light lettering on dark material and dark lettering on light material; readable at app-thumbnail size"
        ),
        plaque_material_rule=(
            f"Match the plaque to the same exact {panel_material} used by both text boxes; vary only its shape, edge, mounting, and finish"
        ),
        plaque_shape=_text(row, "Plaque Shape", "plaque_shape") or _choose(card_id, "plaque_shape", PLAQUE_SHAPES),
        plaque_edge=_text(row, "Plaque Edge", "plaque_edge") or _choose(card_id, "plaque_edge", PLAQUE_EDGES),
        plaque_mounting=_text(row, "Plaque Mounting", "plaque_mounting")
        or _choose(card_id, "plaque_mounting", PLAQUE_MOUNTS),
    )


def augment_prompt(row: Mapping[str, str], base_prompt: str, mode: str = "art-plate") -> tuple[str, V8Rules]:
    rules = resolve_v8_rules(row)
    card_id = _text(row, "Card ID", "Card_ID", "id")
    subject = _text(row, "Subject", "Species", "species")
    text_instruction = (
        "Build finished blank title, lower information, and number-plaque surfaces. The title and lower panel must use the exact same organic material. Render no letters, numbers, symbols, logos, or fake text anywhere."
        if mode == "art-plate"
        else "This is a proof mode; exact typography is still applied after generation."
    )

    block = f"""
ZOO V8 LOCKED ART-PLATE DIRECTIVE — {card_id} — {subject}
- Create a premium natural-history collectible card art plate.
- POP COLOR: one dominant family, {rules.pop_color_family}, sampled from {rules.pop_color_source}.
- POP PLACEMENT: distinct outer surround behind the asymmetrical natural frame, irregularly visible across about {rules.pop_color_visibility_target}% of total perimeter area; {rules.pop_color_distribution}; {rules.pop_color_intensity}.
- Do not create an equal-width border. Partially obscure the surround with habitat-correct natural elements.
- TITLE SURFACE: blank straight horizontal habitat-matched material at the top.
- LOWER SURFACE: blank integrated habitat-matched material using the Fennec Fox hierarchy and generous clean text-safe area.
- SHARED TEXT-BOX MATERIAL — HARD LOCK: {rules.shared_panel_material_rule}.
- PLAQUE: blank material-matched {rules.plaque_shape}, {rules.plaque_edge}, {rules.plaque_mounting}; {rules.plaque_material_rule}.
- SUBJECT: accurate {subject}, large and dominant, natural pose, correct habitat, realistic refined painterly finish.
- GEOMETRY: portrait 3:4 generation canvas, central 5:7 crop safe; keep anatomy and all blank panels inside the central 94% width.
- TEXT MODE: {text_instruction}
- REJECT: typography, glyphs, numbers, logos, footer branding, compass medallions, parchment default, uniform border, neon, rainbow, glow, chrome, plastic, mismatched title/lower-panel material, duplicated panels, obstructed anatomy.
""".strip()

    return f"{base_prompt.strip()}\n\n{block}", rules
