from __future__ import annotations

import unittest

from nodes.custom.style_prompt_preset import GuaguaStylePromptPresetNode
from nodes.style_library import get_style_preset, load_style_presets


class StylePromptPresetNodeTests(unittest.TestCase):
    def setUp(self):
        self.node = GuaguaStylePromptPresetNode()

    def test_style_library_contains_expected_number_of_presets(self):
        presets = load_style_presets()
        self.assertEqual(len(presets), 30)

    def test_empty_category_or_preset_passthroughs_base_prompt(self):
        self.assertEqual(
            self.node.build_prompt("a frog astronaut", "空", "空"),
            ("a frog astronaut",),
        )
        self.assertEqual(
            self.node.build_prompt("a frog astronaut", "真人摄影", "空"),
            ("a frog astronaut",),
        )

    def test_valid_preset_appends_english_suffix(self):
        result = self.node.build_prompt("a frog astronaut", "动漫", "电影感动漫")
        self.assertIn("a frog astronaut", result[0])
        self.assertIn("cinematic anime frame", result[0])

    def test_american_comic_style_is_available(self):
        result = self.node.build_prompt("a frog superhero", "动漫", "美漫风格")
        self.assertIn("a frog superhero", result[0])
        self.assertIn("American comic book illustration", result[0])

    def test_superhero_comic_style_is_available(self):
        result = self.node.build_prompt("a frog guardian", "动漫", "超级英雄美漫")
        self.assertIn("a frog guardian", result[0])
        self.assertIn("superhero comic illustration", result[0])

    def test_category_preset_mismatch_raises_cleanly(self):
        with self.assertRaises(KeyError):
            get_style_preset("3D", "电影感动漫")


if __name__ == "__main__":
    unittest.main()
