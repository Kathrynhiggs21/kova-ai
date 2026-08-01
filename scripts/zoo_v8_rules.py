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
    {
        "id": "forest_rust",
        "keywords": ("forest", "bamboo", "woodland", "panda", "tiger", "fox", "mammal"),
        "family": "warm rust red, muted bamboo green, and amber-brown",
        "source": "fur, bark, and forest foliage",
    },
    {
        "id": "desert_apricot",
        "keywords": ("desert", "sand", "dune", "fennec", "arid", "savanna"),
        "family": "sunlit apricot, sand-gold, and warm ochre",
        "source": "sand, sunlit fur, and dry habitat tones",
    },
    {
        "id": "wetland_teal",
        "keywords": ("water", "river", "ocean", "reef", "fish", "aquatic", "wetland"),
        "family": "deep teal, mineral blue-green, and muted turquoise",
        "source": "water, scales, and aquatic vegetation",
    },
    {
        "id": "botanical_berry",
        "keywords": ("flower", "plant", "botanical", "orchid", "butterfly", "pollinator", "garden"),
        "family": "berry, petal coral, and leaf green",
        "source": "petals, wings, leaves, and botanical details",
    },
    {
        "id": "stone_moss",
        "keywords": ("stone", "rock", "mountain", "alpine", "reptile", "amphibian", "moss"),
        "family": "moss green, slate blue, and mineral amber",
        "source": "stone, moss, scales, and shaded habitat",
    },
    {
        "id": "sky_gold",
        "keywords": ("bird", "eagle", "raptor", "sky", "aviary", "feather"),
        "family": "sky blue, feather gold, and muted sunset copper",
        "source": "feathers, open sky, and sunlit habitat",
    },
    {
        "id": "archive_bronze",
        "keywords": ("history", "zoo", "archive", "map", "utility", "story"),
        "family": "archive green, aged bronze, and museum burgundy",
        "source": "historic signage, archival materials, and aged metal",
    },
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
        if match:
            parsed = int(match.group(1))
            if 8 <= parsed <= 18:
                return parsed
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
        for key in (
            "Subject",
            "Species",
            "species",
            "Habitat",
            "Category",
            "Class",
            "Prompt",
            "Prompt_V7_1",
            "prompt",
        )
    ).lower()

    explicit_family = _text(row, "Pop Color Family", "pop_color_family")
    explicit_source = _text(row, "Pop Color Source", "pop_color_source")

    ranked = []
    for palette in PALETTES:
        score = sum(1 for word in palette["keywords"] if word in searchable)
        ranked.append((score, palette))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    palette = ranked[0][1] if ranked[0][0] else _choose(card_id, "palette", PALETTES)

    panel_material = _text(
        row,
        "Panel Material",
        "Title Material",
        "Frame Material",
        "Material Family",
        "panel_material",
    ) or "the card's habitat-matched organic material family"

    visibility = _parse_visibility(
        _text(row, "Pop Color Visibility", "pop_color_visibility_target"), card_id
    )

    return V8Rules(
        pop_color_family=explicit_family or palette["family"],
        pop_color_source=explicit_source or palette["source"],
        pop_color_visibility_target=visibility,
        pop_color_intensity=_text(row, "Pop Color Intensity", "pop_color_intensity")
        or _choose(card_id, "intensity", INTENSITIES),
        pop_color_distribution=_text(row, "Pop Color Distribution", "pop_color_distribution")
        or _choose(card_id, "distribution", DISTRIBUTIONS),
        title_rule=(
            "ALL CAPS; at least 80% of the Red Panda reference title character with larger cap forms, "
            "deep carved dimensional shadowing, retained ornamental intricacy, and about 20% hand-carved soap-like irregularity"
        ),
        info_panel_rule=(
            "Use the Fennec Fox reference lower-panel hierarchy and spacing: scientific name first, compact stat line, "
            "separate identifier/fun-fact areas, and the canonical number plaque in its safe zone"
        ),
        text_contrast_rule=(
            "Use light lettering on dark material and dark lettering on light material; preserve strong legibility at app-thumbnail size"
        ),
        plaque_material_rule=f"Match the plaque to {panel_material}; never use a universal unrelated badge material",
        plaque_shape=_text(row, "Plaque Shape", "plaque_shape") or _choose(card_id, "plaque_shape", PLAQUE_SHAPES),
        plaque_edge=_text(row, "Plaque Edge", "plaque_edge") or _choose(card_id, "plaque_edge", PLAQUE_EDGES),
        plaque_mounting=_text(row, "Plaque Mounting", "plaque_mounting")
        or _choose(card_id, "plaque_mounting", PLAQUE_MOUNTS),
    )


def validate_row(row: Mapping[str, str], base_prompt: str) -> list[str]:
    problems: list[str] = []
    card_id = _text(row, "Card ID", "Card_ID", "id")
    if not card_id:
        problems.append("blank canonical card ID")
    if not base_prompt.strip():
        problems.append(f"{card_id or 'unknown card'} has no prompt")

    rules = resolve_v8_rules(row)
    if not 8 <= rules.pop_color_visibility_target <= 18:
        problems.append(f"{card_id}: pop-color visibility target must be 8–18%")

    prompt_lower = base_prompt.lower()
    for term in PROHIBITED_STYLE_TERMS:
        if term in prompt_lower:
            problems.append(f"{card_id}: prohibited style term in source prompt: {term}")
    return problems


def augment_prompt(row: Mapping[str, str], base_prompt: str, mode: str = "art-plate") -> tuple[str, V8Rules]:
    rules = resolve_v8_rules(row)
    card_id = _text(row, "Card ID", "Card_ID", "id")
    subject = _text(row, "Subject", "Species", "species")

    if mode == "art-plate":
        text_instruction = (
            "Construct the title plank, lower information panel, and number plaque as finished blank physical materials. "
            "Do not render final small lettering; leave clean usable surfaces for deterministic text composition."
        )
    else:
        text_instruction = (
            "Render only the exact supplied title and card ID; keep all other small copy simple and legible. "
            "This full-card mode is for proofs, not final 517-card typography."
        )

    block = f"""

ZOO V8 LOCKED PRODUCTION DIRECTIVE — CARD {card_id} — {subject}
- POP COLOR: Use one dominant family: {rules.pop_color_family}, sampled from {rules.pop_color_source}.
- POP PLACEMENT: It is a distinct outer surround behind the asymmetrical natural frame, visibly exposed across about {rules.pop_color_visibility_target}% of the perimeter. Distribution: {rules.pop_color_distribution}. Intensity: {rules.pop_color_intensity}.
- POP RESTRICTIONS: Partially obscure the color with habitat-correct framing. Never turn it into a uniform border, neon glow, full-card wash, title-plank fill, or lower-panel fill.
- TITLE: {rules.title_rule}.
- LOWER PANEL: {rules.info_panel_rule}.
- CONTRAST: {rules.text_contrast_rule}.
- NUMBER PLAQUE: {rules.plaque_material_rule}; use a {rules.plaque_shape}, {rules.plaque_edge}, {rules.plaque_mounting}. Exact ID appears once only.
- GEOMETRY: Compose for a 3:4 generation canvas that will be center-cropped to exact 5:7. Keep all essential subject anatomy, title structure, lower panel, and plaque inside the central 94% width safe area.
- TEXT MODE: {text_instruction}
- REJECT: flat uniform borders, hidden pop color, mismatched panels, plastic/chrome rims, neon, rainbow, glow, fake text, duplicated IDs, or obstructed subject anatomy.
""".strip()

    return f"{base_prompt.strip()}\n\n{block}", rules
