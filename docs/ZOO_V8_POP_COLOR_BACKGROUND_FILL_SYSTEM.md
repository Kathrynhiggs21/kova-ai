# Zoo V8 — Pop Color Background Fill System

**Status:** LOCKED  
**Applies to:** design specification, prompt generation, automated QA, renderer metadata, and human visual QA.

## Locked rule

The pop color is a **distinct subject- or habitat-derived outer surround layer**. It sits behind the natural frame, remains visible through roughly **8–18% of the card perimeter**, and never replaces the title plank or lower information-panel materials.

## 1. Design specification

### Layer order

1. outer pop-color surround
2. asymmetrical organic habitat frame
3. habitat image and subject
4. title plank
5. lower information panel
6. category/species identifiers and number plaque

The pop-color surround must read as its own layer. It is not merely a color cast applied to the complete card.

### Color source

Select one dominant family from the subject or habitat: fur, feathers, scales, petals, leaves, bark, sand, stone, water, sky, moss, coral, or another natural cue. The selected family must support the card rather than compete with the subject.

### Required visibility

- visible through approximately 8–18% of the perimeter zone
- unevenly distributed through corners, edge openings, and gaps in the natural frame
- partially covered by branches, bark, stone, roots, leaves, vines, moss, or other habitat-correct materials
- clearly visible at thumbnail size without becoming a hard border

### Independence from panels

The pop color may influence small accent details, but it must not become:

- the title-plank material
- the lower information-panel material
- a flat rectangle behind body copy
- a glowing outline
- a uniform rim

Title and lower panel retain their habitat-matched organic material family.

### Rejection conditions

Reject neon, rainbow, glow, flat poster borders, uniform symmetry, full-card color washes, unrelated accent colors, pop color over the subject, and pop color that replaces natural materials.

## 2. Prompt-generator contract

Every production prompt receives a resolved block containing:

- `pop_color_family`
- `pop_color_source`
- `pop_color_visibility_target`
- `pop_color_intensity`
- `pop_color_distribution`

The resolver is deterministic: the same canonical card ID and source data produce the same result unless an explicit workbook value overrides it.

Required prompt language:

> Use one dominant pop-color family sampled from the subject or habitat. Place it as a distinct outer surround behind the asymmetrical natural frame. Keep approximately 8–18% of the perimeter visibly exposed through irregular corners and frame openings. Partially obscure it with habitat materials. Never use it as a uniform border, glow, title-plank fill, or lower information-panel material.

## 3. QA checklist

A card passes only when all conditions are true:

- [ ] one dominant pop-color family is present
- [ ] color is related to the subject or habitat
- [ ] color sits behind the natural frame
- [ ] visible exposure falls within the 8–18% target band or receives a documented human override
- [ ] exposure is uneven and organically distributed
- [ ] natural framing partially obscures the color
- [ ] title and information panels retain separate organic materials
- [ ] subject, title, facts, and plaque remain unobstructed
- [ ] no glow, neon, rainbow, flat border, or synthetic plastic appearance
- [ ] the accent remains visible in the app thumbnail

Automatic prompt QA blocks blank IDs, invalid percentage targets, prohibited styling language, and missing prompts before paid rendering.

## 4. Renderer rules

The renderer must:

1. resolve V8 rules before calling Gemini;
2. append the locked prompt block to the source prompt;
3. generate at supported 3:4 geometry and crop safely to exact 5:7;
4. keep all important content inside the central safe area before cropping;
5. store resolved pop-color metadata in JSONL status records;
6. skip completed files;
7. retry transient errors;
8. support dry-run prompt review;
9. fail preflight before paid rendering when rule validation fails.

## Related V8 controls

- all-caps title profile: approximately 80% Red Panda reference character and 20% hand-carved organic irregularity
- dimensional carving, material shadowing, and retained title intricacy
- Fennec Fox lower information-panel layout across front cards
- automatic light text on dark materials and dark text on light materials
- material-matched number plaques with variable shape, edge, mounting, and finish

## Final summary

**Subject-derived color. Distinct outer layer. Eight to eighteen percent visible. Partially hidden by nature. Never substituted for the title or information-panel material.**
