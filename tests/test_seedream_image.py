from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nodes.custom.seedream_image import GuaguaSeedreamImageNode


class SeedreamImageNodeTests(unittest.TestCase):
    def setUp(self):
        self.node = GuaguaSeedreamImageNode()

    def test_generate_image_builds_expected_request(self):
        captured: dict[str, object] = {}

        class FakeImages:
            def generate(self, **kwargs):
                captured.update(kwargs)
                return {"data": [{"url": "https://example.com/image.png"}]}

        fake_client = SimpleNamespace(images=FakeImages())

        with patch("nodes.custom.seedream_image.create_ark_client", return_value=fake_client), patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ):
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="a frog astronaut",
                model="doubao-seedream-5-0-lite-260128",
                size_preset="16:9",
                seed=123,
                guidance_scale=3.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(captured["model"], "doubao-seedream-5-0-lite-260128")
        self.assertEqual(captured["prompt"], "a frog astronaut")
        self.assertEqual(captured["size"], "16:9")
        self.assertEqual(captured["n"], 1)
        self.assertEqual(captured["seed"], 123)
        self.assertEqual(captured["guidance_scale"], 3.5)
        self.assertEqual(captured["watermark"], True)
        self.assertEqual(captured["response_format"], "url")

    def test_generate_image_raises_when_response_has_no_url(self):
        class FakeImages:
            def generate(self, **kwargs):
                return {"data": []}

        fake_client = SimpleNamespace(images=FakeImages())

        with patch("nodes.custom.seedream_image.create_ark_client", return_value=fake_client):
            with self.assertRaises(RuntimeError) as context:
                self.node.generate_image(
                    api_key="ark-key",
                    prompt="a frog astronaut",
                    model="doubao-seedream-5-0-lite-260128",
                    size_preset="1:1",
                    seed=0,
                    guidance_scale=2.5,
                    watermark=False,
                )

        self.assertIn("returned no image URL", str(context.exception))

    def test_generate_image_surfaces_auth_failure_cleanly(self):
        with patch(
            "nodes.custom.seedream_image.create_ark_client",
            side_effect=RuntimeError("Invalid API key"),
        ):
            with self.assertRaises(RuntimeError) as context:
                self.node.generate_image(
                    api_key="bad-key",
                    prompt="a frog astronaut",
                    model="doubao-seedream-5-0-lite-260128",
                    size_preset="adaptive",
                    seed=0,
                    guidance_scale=2.5,
                    watermark=True,
                )

        self.assertIn("Seedream 5.0 request failed", str(context.exception))
        self.assertIn("Invalid API key", str(context.exception))


if __name__ == "__main__":
    unittest.main()
