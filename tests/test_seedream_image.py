from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nodes.custom.seedream_image import GuaguaSeedreamImageNode, SEEDREAM_MODELS


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
                resolution="2K",
                aspect_ratio="16:9",
                output_format="png",
                seed=123,
                guidance_scale=3.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(captured["model"], "doubao-seedream-5-0-lite-260128")
        self.assertEqual(captured["prompt"], "a frog astronaut")
        self.assertEqual(captured["size"], "2K")
        self.assertNotIn("seed", captured)
        self.assertEqual(captured["watermark"], True)
        self.assertEqual(captured["output_format"], "png")

    def test_supported_models_include_seedream_45_but_not_40(self):
        self.assertIn("doubao-seedream-4-5-251128", SEEDREAM_MODELS)
        self.assertNotIn("doubao-seedream-4-0-250828", SEEDREAM_MODELS)

    def test_generate_image_supports_optional_image_input(self):
        captured: dict[str, object] = {}

        class FakeImages:
            def generate(self, **kwargs):
                captured.update(kwargs)
                return {"data": [{"url": "https://example.com/image.png"}]}

        fake_client = SimpleNamespace(images=FakeImages())

        with patch("nodes.custom.seedream_image.create_ark_client", return_value=fake_client), patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=["data:image/png;base64,abc123"],
        ):
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="edit this frog into a superhero poster",
                model="doubao-seedream-5-0-260128",
                resolution="3K",
                aspect_ratio="1:1",
                output_format="jpeg",
                seed=0,
                guidance_scale=4.0,
                watermark=False,
                image="fake-image-tensor",
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(captured["size"], "3K")
        self.assertEqual(captured["image"], "data:image/png;base64,abc123")
        self.assertEqual(captured["output_format"], "jpeg")
        self.assertNotIn("sequential_image_generation", captured)

    def test_generate_image_supports_multi_image_batches(self):
        captured: dict[str, object] = {}

        class FakeImages:
            def generate(self, **kwargs):
                captured.update(kwargs)
                return {"data": [{"url": "https://example.com/image.png"}]}

        fake_client = SimpleNamespace(images=FakeImages())

        with patch("nodes.custom.seedream_image.create_ark_client", return_value=fake_client), patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=["data:image/png;base64,img1", "data:image/png;base64,img2"],
        ):
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="merge two frog references into one poster",
                model="doubao-seedream-5-0-260128",
                resolution="2K",
                aspect_ratio="4:3",
                output_format="png",
                seed=0,
                guidance_scale=3.0,
                watermark=False,
                image="fake-image-batch",
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(
            captured["image"],
            ["data:image/png;base64,img1", "data:image/png;base64,img2"],
        )
        self.assertEqual(captured["sequential_image_generation"], "disabled")

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
                    resolution="2K",
                    aspect_ratio="1:1",
                    output_format="png",
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
                    resolution="2K",
                    aspect_ratio="1:1",
                    output_format="png",
                    seed=0,
                    guidance_scale=2.5,
                    watermark=True,
                )

        self.assertIn("Seedream 5.0 request failed", str(context.exception))
        self.assertIn("Invalid API key", str(context.exception))

    def test_generate_image_retries_on_connection_error(self):
        attempts = {"count": 0}

        class FakeImages:
            def generate(self, **kwargs):
                attempts["count"] += 1
                if attempts["count"] < 3:
                    raise RuntimeError("Connection error., request_id: retry-me")
                return {"data": [{"url": "https://example.com/image.png"}]}

        fake_client = SimpleNamespace(images=FakeImages())

        with patch("nodes.custom.seedream_image.create_ark_client", return_value=fake_client), patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch("nodes.custom.seedream_image.time.sleep"):
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="a frog astronaut",
                model="doubao-seedream-5-0-lite-260128",
                resolution="2K",
                aspect_ratio="1:1",
                output_format="png",
                seed=0,
                guidance_scale=2.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(attempts["count"], 3)

    def test_too_many_reference_images_raises_cleanly(self):
        with patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=[f"data:image/png;base64,img{i}" for i in range(11)],
        ):
            with self.assertRaises(ValueError) as context:
                self.node._prepare_reference_images("fake-image-batch")

        self.assertIn("at most 10 reference images", str(context.exception))

    def test_single_reference_image_returns_string_payload(self):
        with patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=["data:image/png;base64,single"],
        ):
            payload = self.node._prepare_reference_images("fake-image")

        self.assertEqual(payload, "data:image/png;base64,single")


if __name__ == "__main__":
    unittest.main()
