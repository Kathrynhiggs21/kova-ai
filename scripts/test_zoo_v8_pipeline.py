from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from zoo_v8_pipeline import APP_SIZE, MASTER_SIZE, THUMB_SIZE, merge_sources, read_csv, select_rows


def test_join_first_16_and_card_families_ready():
    base = Path(__file__).resolve().parent.parent
    rows = merge_sources(
        read_csv(base / "data" / "MASTER_CARD_PRODUCTION_DATABASE.csv"),
        read_csv(base / "data" / "MASTER_SPECIES_DATABASE.csv"),
    )
    assert len(rows) == 517
    assert len({row["Card ID"] for row in rows}) == 517

    first = select_rows(rows, "", 0, 16, False)
    assert all(row["Data Status"] == "READY" for row in first)
    assert first[0]["Subject"] == "Aye-Aye"
    assert first[13]["Subject"] == "Fennec Fox"
    assert first[0]["Category Back ID"] == "BACK-01"

    mixed = select_rows(rows, "X026,BACK-01", 0, 0, False)
    assert mixed[0]["Data Status"] == "READY"
    assert "utility" in mixed[0]["Type"].lower()
    assert mixed[1]["Type"] == "Card Back"


def test_output_geometry_constants():
    assert MASTER_SIZE == (2250, 3150)
    assert APP_SIZE == (1000, 1400)
    assert THUMB_SIZE == (360, 504)
