from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nodes.custom.qwen_multimodal import GuaguaQwenMultimodalNode


class FakeGeneration:
    def __init__(self, captured):
        self.captured = captured

    def call(self, **kwargs):
        self.captured["generation"] = kwargs
        return {
            "output": {
                "choices": [
                    {
                        "message": {
                            "content": "text reply",
                        }
                    }
                ]
            }
        }


class FakeMultiModalConversation:
    def __init__(self, captured):
        self.captured = captured

    def call(self, **kwargs):
        self.captured["multimodal"] = kwargs
        return {
            "output": {
                "choices": [
                    {
                        "message": {
                            "content": [{"text": "multimodal reply"}],
                        }
                    }
                ]
            }
        }


class QwenMultimodalNodeTests(unittest.TestCase):
    def setUp(self):
        self.node = GuaguaQwenMultimodalNode()

    def test_text_chat_uses_generation_api(self):
        captured = {}
        fake_dashscope = SimpleNamespace(
            Generation=FakeGeneration(captured),
            MultiModalConversation=FakeMultiModalConversation(captured),
        )

        with patch("nodes.custom.qwen_multimodal.configure_dashscope", return_value=fake_dashscope):
            result = self.node.run(
                api_key="dashscope-key",
                task_mode="text_chat",
                model="qwen-plus",
                system_prompt="You are helpful.",
                user_prompt="Hello there",
            )

        self.assertEqual(result, ("text reply",))
        self.assertEqual(captured["generation"]["model"], "qwen-plus")
        self.assertEqual(captured["generation"]["messages"][0]["role"], "system")
        self.assertEqual(captured["generation"]["messages"][1]["content"], "Hello there")

    def test_image_analysis_prefers_connected_image_input(self):
        captured = {}
        fake_dashscope = SimpleNamespace(
            Generation=FakeGeneration(captured),
            MultiModalConversation=FakeMultiModalConversation(captured),
        )

        with patch("nodes.custom.qwen_multimodal.configure_dashscope", return_value=fake_dashscope), patch(
            "nodes.custom.qwen_multimodal.comfy_image_to_temp_file",
            return_value=r"C:\temp\guagua-image.png",
        ), patch("nodes.custom.qwen_multimodal.safe_remove_file") as remove_file:
            result = self.node.run(
                api_key="dashscope-key",
                task_mode="image_analysis",
                model="qwen3-vl-8b-instruct",
                system_prompt="Describe the image.",
                user_prompt="What do you see?",
                image="fake-image-tensor",
                image_path_or_url="https://example.com/ignored.png",
            )

        self.assertEqual(result, ("multimodal reply",))
        content = captured["multimodal"]["messages"][-1]["content"]
        self.assertEqual(content[0]["image"], r"C:\temp\guagua-image.png")
        remove_file.assert_called_once_with(r"C:\temp\guagua-image.png")

    def test_video_analysis_uses_video_reference(self):
        captured = {}
        fake_dashscope = SimpleNamespace(
            Generation=FakeGeneration(captured),
            MultiModalConversation=FakeMultiModalConversation(captured),
        )

        with patch("nodes.custom.qwen_multimodal.configure_dashscope", return_value=fake_dashscope), patch(
            "nodes.custom.qwen_multimodal.normalize_media_reference",
            return_value=r"C:\videos\clip.mp4",
        ):
            result = self.node.run(
                api_key="dashscope-key",
                task_mode="video_analysis",
                model="qwen3-vl-30b-a3b-instruct",
                system_prompt="Summarize the video.",
                user_prompt="What happens in this clip?",
                video_path_or_url=r"C:\videos\clip.mp4",
            )

        self.assertEqual(result, ("multimodal reply",))
        video_item = captured["multimodal"]["messages"][-1]["content"][0]
        self.assertEqual(video_item["video"], r"C:\videos\clip.mp4")
        self.assertEqual(video_item["fps"], 2.0)

    def test_task_and_model_combination_is_validated(self):
        with self.assertRaises(RuntimeError) as context:
            self.node.run(
                api_key="dashscope-key",
                task_mode="text_chat",
                model="qwen3-vl-8b-instruct",
                system_prompt="You are helpful.",
                user_prompt="Hello there",
            )

        self.assertIn("text_chat requires one of these models", str(context.exception))


if __name__ == "__main__":
    unittest.main()
