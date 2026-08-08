from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def extract_literal_slot(build_script: Path) -> str:
    tree = ast.parse(build_script.read_text(encoding="utf-8"), filename=str(build_script))
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        values = [item.value if isinstance(item, ast.Constant) else None for item in node.elts]
        for index, value in enumerate(values[:-1]):
            if value == "--slot" and isinstance(values[index + 1], str):
                found.add(values[index + 1])
    if len(found) != 1:
        raise AssertionError(f"expected one literal --slot in {build_script}, found {found}")
    return found.pop()


class ExampleTargetProfileTests(unittest.TestCase):
    EXPECTED = {
        "color_cycle": "SY",
        "bad_apple_player": "G1",
        "mobigo_celeste": "G1",
    }

    def test_build_scripts_name_the_intended_profile(self) -> None:
        for example, expected in self.EXPECTED.items():
            with self.subTest(example=example):
                actual = extract_literal_slot(ROOT / "examples" / example / "build.py")
                self.assertEqual(actual, expected)

    def test_maintained_example_guides_match_build_profiles(self) -> None:
        table = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        complete = (ROOT / "docs" / "examples" / "complete-projects.md").read_text(
            encoding="utf-8"
        )
        index = (ROOT / "docs" / "examples" / "index.md").read_text(encoding="utf-8")
        color = (ROOT / "examples" / "color_cycle" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("| `color_cycle/` | SY |", table)
        self.assertIn("| `mobigo_celeste/` | legacy G1 |", table)
        self.assertIn("| `bad_apple_player/` | legacy G1 |", table)
        self.assertIn("`build/color-cycle/ColorCycle.MBA`, linked for SY", complete)
        self.assertIn("This minimal SY sample", color)
        self.assertIn("Color Cycle is the maintained low-level SY example", index)
        self.assertNotIn(
            "Color Cycle, the monochrome movie player, and MobiGo Celeste are maintained\nlegacy G1",
            index,
        )


if __name__ == "__main__":
    unittest.main()
