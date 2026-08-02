from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from zoo_v8_rules import augment_prompt, resolve_v8_rules, validate_row  # noqa: E402


class ZooV8RulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {
            "Card ID": "A001",
            "Subject": "Bengal Tiger",
            "Habitat": "tropical forest",
            "Category": "Mammal",
            "Panel Material": "dark carved rainforest wood",
            "Prompt": "Premium museum-quality wildlife collector card with a Bengal tiger in tropical forest habitat.",
        }

    def test_resolution_is_deterministic(self) -> None:
        first = resolve_v8_rules(self.row)
        second = resolve_v8_rules(self.row)
        self.assertEqual(first, second)

    def test_pop_visibility_is_locked_to_range(self) -> None:
        rules = resolve_v8_rules(self.row)
        self.assertGreaterEqual(rules.pop_color_visibility_target, 8)
        self.assertLessEqual(rules.pop_color_visibility_target, 18)

    def test_prompt_contains_locked_visual_rules(self) -> None:
        prompt, rules = augment_prompt(self.row, self.row["Prompt"], mode="art-plate")
        self.assertIn("distinct outer surround", prompt)
        self.assertIn("ALL CAPS", prompt)
        self.assertIn("Fennec Fox reference lower-panel hierarchy", prompt)
        self.assertIn("Exact ID appears once only", prompt)
        self.assertIn(str(rules.pop_color_visibility_target), prompt)

    def test_valid_row_passes_preflight(self) -> None:
        self.assertEqual(validate_row(self.row, self.row["Prompt"]), [])

    def test_blank_id_is_rejected(self) -> None:
        broken = dict(self.row)
        broken["Card ID"] = ""
        problems = validate_row(broken, broken["Prompt"])
        self.assertTrue(any("blank canonical card ID" in item for item in problems))

    def test_prohibited_style_language_is_rejected(self) -> None:
        prompt = self.row["Prompt"] + " Add a neon glowing border."
        problems = validate_row(self.row, prompt)
        self.assertTrue(any("prohibited style term" in item for item in problems))


if __name__ == "__main__":
    unittest.main()
