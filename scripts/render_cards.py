#!/usr/bin/env python3
"""Kova AI Zoo V8 image renderer.

Reads the existing 517-card prompt CSV, resolves the locked V8 visual rules,
generates with Gemini, crops supported 3:4 output to exact 5:7, resumes safely,
and records JSONL production metadata.
"""

from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

from google import genai
from PIL import Image

from zoo_v8_rules import augment_prompt, validate_row

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_DIR = Path(__file__).resolve().parent.parent
RENDERS_DIR = BASE_DIR / "renders" / "v8"
REPORTS_DIR = BASE_DIR / "reports" / "v8"
STATUS_LOCK = Lock()

MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
API_KEY = os.getenv("GEMINI_API_KEY")


def field(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value and str(value).strip():
            return str(value).strip()
    return ""


def safe_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", value)).strip("_")


def append_jsonl(path: Path, record: dict) -> None:
    with STATUS_LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_image_bytes(interaction) -> bytes:
    output_image = getattr(interaction, "output_image", None)
    data = getattr(output_image, "data", None) if output_image is not None else None
    if data:
        return base64.b64decode(data) if isinstance(data, str) else bytes(data)

    for step in getattr(interaction, "steps", []) or []:
        for block in getattr(step, "content", []) or []:
            block_data = getattr(block, "data", None)
            if getattr(block, "type", None) == "image" and block_data:
                return base64.b64decode(block_data) if isinstance(block_data, str) else bytes(block_data)
    raise RuntimeError("Gemini response did not contain an image")


def save_exact_5x7(image_bytes: bytes, output_path: Path) -> tuple[int, int]:
    """Center-crop Gemini's supported 3:4 canvas to exact 5:7."""
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
        width, height = image.size
        target_ratio = 5 / 7
        source_ratio = width / height

        if source_ratio > target_ratio:
            new_width = round(height * target_ratio)
            left = max(0, (width - new_width) // 2)
            box = (left, 0, left + new_width, height)
        else:
            new_height = round(width / target_ratio)
            top = max(0, (height - new_height) // 2)
            box = (0, top, width, top + new_height)

        cropped = image.crop(box)
        cropped.save(output_path, format="PNG", optimize=True)
        return cropped.size


def output_filename(row: dict[str, str], mode: str) -> str:
    card_id = field(row, "Card ID", "Card_ID", "id")
    subject = field(row, "Subject", "Species", "species") or "Card"
    card_type = field(row, "Card Type", "Type", "card_type").lower()
    face = "back" if "back" in card_type else "front"
    suffix = "art_plate" if mode == "art-plate" else "proof"
    return f"{safe_name(card_id)}_{safe_name(subject)}_{face}_V8_{suffix}.png"


def render_one(
    row: dict[str, str],
    output_dir: Path,
    status_path: Path,
    mode: str,
    image_size: str,
    retries: int,
) -> dict:
    card_id = field(row, "Card ID", "Card_ID", "id")
    subject = field(row, "Subject", "Species", "species")
    base_prompt = field(row, "Prompt_V8", "Prompt", "Prompt_V7_1", "prompt")
    prompt, rules = augment_prompt(row, base_prompt, mode=mode)
    output_path = output_dir / output_filename(row, mode)

    if output_path.exists() and output_path.stat().st_size > 0:
        record = {
            "card_id": card_id,
            "subject": subject,
            "status": "completed",
            "skipped": True,
            "file": str(output_path),
            "rules": rules.to_dict(),
        }
        append_jsonl(status_path, record)
        return record

    last_error = ""
    for attempt in range(1, retries + 2):
        try:
            client = genai.Client(api_key=API_KEY)
            interaction = client.interactions.create(
                model=MODEL_NAME,
                input=prompt,
                response_format={
                    "type": "image",
                    "mime_type": "image/png",
                    "aspect_ratio": "3:4",
                    "image_size": image_size,
                },
            )
            raw = extract_image_bytes(interaction)
            final_size = save_exact_5x7(raw, output_path)
            record = {
                "card_id": card_id,
                "subject": subject,
                "status": "completed",
                "file": str(output_path),
                "model": MODEL_NAME,
                "mode": mode,
                "requested_size": image_size,
                "final_pixel_size": list(final_size),
                "aspect_ratio": "5:7",
                "attempt": attempt,
                "rules": rules.to_dict(),
            }
            append_jsonl(status_path, record)
            return record
        except Exception as exc:  # SDK error classes vary by release.
            last_error = f"{type(exc).__name__}: {exc}"
            logging.warning("%s attempt %s failed: %s", card_id, attempt, last_error)
            if attempt <= retries:
                time.sleep(min(60, (2**attempt) + random.random() * 3))

    record = {
        "card_id": card_id,
        "subject": subject,
        "status": "failed",
        "model": MODEL_NAME,
        "mode": mode,
        "error": last_error,
        "rules": rules.to_dict(),
    }
    append_jsonl(status_path, record)
    return record


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"CSV contains no rows: {csv_path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Kova AI Zoo V8 Gemini renderer")
    parser.add_argument("--csv", type=Path, default=BASE_DIR / "data" / "v7.1_zoo_prompts.csv")
    parser.add_argument("--limit", type=int, default=10, help="Cards to process; 0 means all")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--image-size", choices=("1K", "2K", "4K"), default="2K")
    parser.add_argument("--mode", choices=("art-plate", "full-card"), default="art-plate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not API_KEY and not args.dry_run:
        raise SystemExit("Missing GEMINI_API_KEY")

    rows = load_rows(args.csv)
    rows = rows[args.offset :]
    if args.limit > 0:
        rows = rows[: args.limit]

    problems: list[str] = []
    resolved: list[tuple[dict[str, str], str, dict]] = []
    for row in rows:
        base_prompt = field(row, "Prompt_V8", "Prompt", "Prompt_V7_1", "prompt")
        problems.extend(validate_row(row, base_prompt))
        prompt, rules = augment_prompt(row, base_prompt, mode=args.mode)
        resolved.append((row, prompt, rules.to_dict()))

    if problems:
        for problem in problems:
            logging.error("PRELIGHT: %s", problem)
        raise SystemExit(f"V8 preflight failed with {len(problems)} problem(s)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        preview = REPORTS_DIR / "prompt_preview.jsonl"
        with preview.open("w", encoding="utf-8") as handle:
            for row, prompt, rules in resolved:
                handle.write(
                    json.dumps(
                        {
                            "card_id": field(row, "Card ID", "Card_ID", "id"),
                            "subject": field(row, "Subject", "Species", "species"),
                            "prompt": prompt,
                            "rules": rules,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        logging.info("Dry run passed. Prompt preview: %s", preview)
        return 0

    output_dir = RENDERS_DIR / args.mode
    output_dir.mkdir(parents=True, exist_ok=True)
    status_path = REPORTS_DIR / f"render_status_{args.mode}.jsonl"

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = [
            pool.submit(
                render_one,
                row,
                output_dir,
                status_path,
                args.mode,
                args.image_size,
                args.retries,
            )
            for row in rows
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            logging.info(json.dumps(result, ensure_ascii=False))

    failed = sum(result.get("status") == "failed" for result in results)
    completed = sum(result.get("status") == "completed" for result in results)
    summary = {
        "submitted": len(rows),
        "completed": completed,
        "failed": failed,
        "model": MODEL_NAME,
        "mode": args.mode,
        "aspect_ratio": "5:7",
    }
    (REPORTS_DIR / f"summary_{args.mode}.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    logging.info(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
