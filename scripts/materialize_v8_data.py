#!/usr/bin/env python3
"""Rebuild canonical V8 CSV snapshots from repository-safe compressed parts."""
from __future__ import annotations

import base64
import gzip
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BOOTSTRAP_DIR = BASE_DIR / "data" / "bootstrap"
DATA_DIR = BASE_DIR / "data"
TARGETS = (
    "MASTER_CARD_PRODUCTION_DATABASE.csv",
    "MASTER_SPECIES_DATABASE.csv",
)


def materialize(target_name: str) -> Path:
    parts = sorted(BOOTSTRAP_DIR.glob(f"{target_name}.gz.part*.b64"))
    if not parts:
        raise SystemExit(f"Missing bootstrap parts for {target_name}")
    payload = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    compressed = base64.b64decode(payload, validate=True)
    content = gzip.decompress(compressed)
    target = DATA_DIR / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    print(f"Materialized {target.relative_to(BASE_DIR)} ({len(content)} bytes)")
    return target


def main() -> int:
    for name in TARGETS:
        materialize(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
