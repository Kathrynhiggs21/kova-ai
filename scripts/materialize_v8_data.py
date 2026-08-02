#!/usr/bin/env python3
"""Rebuild canonical V8 CSV snapshots from repository-safe compressed parts."""
from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BOOTSTRAP_DIR = BASE_DIR / "data" / "bootstrap"
DATA_DIR = BASE_DIR / "data"
TARGETS = (
    "MASTER_CARD_PRODUCTION_DATABASE.csv",
    "MASTER_SPECIES_DATABASE.csv",
)

EXPECTED = {
    "MASTER_CARD_PRODUCTION_DATABASE.csv": {
        "content_sha256": "54abe58f94b0cac989b4c30c09d3737873633828e354147421d76a9313f2e5bc",
    },
    "MASTER_SPECIES_DATABASE.csv": {
        "content_sha256": "ce0636bb12d5d26f8468e66536c774e997dc3467aa3e35b3499e706cfa201155",
    },
}


def source_parts(target_name: str) -> list[Path]:
    if target_name == "MASTER_SPECIES_DATABASE.csv":
        return sorted((BOOTSTRAP_DIR / "v2").glob(f"{target_name}.gz.part*.b64"))
    return sorted(BOOTSTRAP_DIR.glob(f"{target_name}.gz.part*.b64"))


def verify(label: str, actual: str, expected: str | None) -> None:
    if expected and actual != expected:
        raise SystemExit(f"{label} checksum mismatch: {actual} != {expected}")


def materialize(target_name: str) -> Path:
    parts = source_parts(target_name)
    if not parts:
        raise SystemExit(f"Missing bootstrap parts for {target_name}")
    payload_parts: list[str] = []
    for part in parts:
        text = part.read_text(encoding="ascii").strip()
        print(f"BOOTSTRAP_PART {part.name} length={len(text)} sha256={hashlib.sha256(text.encode('ascii')).hexdigest()}")
        payload_parts.append(text)
    payload = "".join(payload_parts)
    payload_sha = hashlib.sha256(payload.encode("ascii")).hexdigest()
    print(f"BOOTSTRAP_TOTAL {target_name} length={len(payload)} sha256={payload_sha}")

    compressed = base64.b64decode(payload, validate=True)
    gzip_sha = hashlib.sha256(compressed).hexdigest()
    print(f"BOOTSTRAP_GZIP {target_name} bytes={len(compressed)} sha256={gzip_sha}")

    content = gzip.decompress(compressed)
    content_sha = hashlib.sha256(content).hexdigest()
    verify(f"{target_name} content", content_sha, EXPECTED.get(target_name, {}).get("content_sha256"))
    target = DATA_DIR / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    print(f"Materialized {target.relative_to(BASE_DIR)} ({len(content)} bytes) sha256={content_sha}")
    return target


def main() -> int:
    for name in TARGETS:
        materialize(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
