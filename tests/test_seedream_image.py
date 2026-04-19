from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nodes.custom.seedream_image import (
    GuaguaSeedream50ImageNode,
    GuaguaSeedreamLite45ImageNode,
    SEEDREAM_50_MODEL,
    SEEDREAM_LITE_45_MODELS,
)


class SeedreamImageNodeTests(unittest.TestCase):
    def setUp(self):
        self.node = GuaguaSeedream50ImageNode()
        self.lite_45_node = GuaguaSeedreamLite45ImageNode()

    def test_generate_image_builds_expected_request(self):
        captured: dict[str, object] = {}

        class FakeImages:
            pass

        with patch("nodes.custom.seedream_image.post_ark_json") as post_ark_json, patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ):
            post_ark_json.side_effect = lambda api_key, endpoint_path, payload: (
                captured.update(payload) or {"data": [{"url": "https://example.com/image.png"}]}
            )
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="a frog astronaut",
                resolution="2K",
                aspect_ratio="16:9",
                output_format="png",
                seed=123,
                guidance_scale=3.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(captured["model"], SEEDREAM_50_MODEL)
        self.assertEqual(captured["prompt"], "a frog astronaut")
        self.assertEqual(captured["size"], "2K")
        self.assertNotIn("seed", captured)
        self.assertEqual(captured["watermark"], True)
        self.assertEqual(captured["output_format"], "png")

    def test_split_nodes_expose_expected_models(self):
        self.assertEqual(SEEDREAM_50_MODEL, "doubao-seedream-5-0-260128")
        self.assertEqual(
            SEEDREAM_LITE_45_MODELS,
            ["doubao-seedream-5-0-lite-260128", "doubao-seedream-4-5-251128"],
        )

    def test_generate_image_supports_optional_image_input(self):
        captured: dict[str, object] = {}

        with patch("nodes.custom.seedream_image.post_ark_json") as post_ark_json, patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=["data:image/png;base64,abc123"],
        ):
            post_ark_json.side_effect = lambda api_key, endpoint_path, payload: (
                captured.update(payload) or {"data": [{"url": "https://example.com/image.png"}]}
            )
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="edit this frog into a superhero poster",
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

        with patch("nodes.custom.seedream_image.post_ark_json") as post_ark_json, patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch(
            "nodes.custom.seedream_image.comfy_image_to_data_uris",
            return_value=["data:image/png;base64,img1", "data:image/png;base64,img2"],
        ):
            post_ark_json.side_effect = lambda api_key, endpoint_path, payload: (
                captured.update(payload) or {"data": [{"url": "https://example.com/image.png"}]}
            )
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="merge two frog references into one poster",
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
        with patch("nodes.custom.seedream_image.post_ark_json", return_value={"data": []}):
            with self.assertRaises(RuntimeError) as context:
                self.node.generate_image(
                    api_key="ark-key",
                    prompt="a frog astronaut",
                    resolution="2K",
                    aspect_ratio="1:1",
                    output_format="png",
                    seed=0,
                    guidance_scale=2.5,
                    watermark=False,
                )

        self.assertIn("returned no image URL", str(context.exception))

    def test_generate_image_surfaces_auth_failure_cleanly(self):
        with patch("nodes.custom.seedream_image.post_ark_json", side_effect=RuntimeError("Invalid API key")):
            with self.assertRaises(RuntimeError) as context:
                self.node.generate_image(
                    api_key="bad-key",
                    prompt="a frog astronaut",
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

        def flaky_post(api_key, endpoint_path, payload):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("Connection error., request_id: retry-me")
            return {"data": [{"url": "https://example.com/image.png"}]}

        with patch("nodes.custom.seedream_image.post_ark_json", side_effect=flaky_post), patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ), patch("nodes.custom.seedream_image.time.sleep"):
            result = self.node.generate_image(
                api_key="ark-key",
                prompt="a frog astronaut",
                resolution="2K",
                aspect_ratio="1:1",
                output_format="png",
                seed=0,
                guidance_scale=2.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertEqual(attempts["count"], 3)

    def test_adapt_payload_removes_unsupported_output_format(self):
        payload = {
            "model": SEEDREAM_50_MODEL,
            "prompt": "a frog astronaut",
            "size": "2K",
            "output_format": "png",
            "watermark": True,
        }
        exc = RuntimeError(
            "Error code: 400 - {'error': {'code': 'InvalidParameter', "
            "'message': 'The parameter `output_format` specified in the request is not valid: "
            "the parameter `output_format` is not supported by the current model.'}}"
        )

        adapted = self.node._adapt_payload_for_exception(payload, exc)

        self.assertIsNotNone(adapted)
        self.assertIn("output_format", payload)
        self.assertNotIn("output_format", adapted)

    def test_seedream_45_omits_output_format_by_default(self):
        captured = {}

        with patch("nodes.custom.seedream_image.post_ark_json") as post_ark_json, patch(
            "nodes.custom.seedream_image.download_image_as_tensor",
            return_value="tensor-image",
        ):
            post_ark_json.side_effect = lambda api_key, endpoint_path, payload: (
                captured.update(payload) or {"data": [{"url": "https://example.com/image.png"}]}
            )
            result = self.lite_45_node.generate_image(
                api_key="ark-key",
                prompt="a frog astronaut",
                model="doubao-seedream-4-5-251128",
                resolution="2K",
                aspect_ratio="1:1",
                output_format="png",
                seed=0,
                guidance_scale=2.5,
                watermark=True,
            )

        self.assertEqual(result, ("tensor-image",))
        self.assertNotIn("output_format", captured)

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
