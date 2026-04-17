from __future__ import annotations

from ..api_utils import (
    comfy_image_to_temp_file,
    configure_dashscope,
    ensure_text,
    extract_text_response_content,
    format_api_exception,
    normalize_media_reference,
    safe_remove_file,
)


TASK_MODE_OPTIONS = ["text_chat", "image_analysis", "video_analysis"]
TEXT_MODELS = ["qwen-plus", "qwen-turbo", "qwen-max"]
VISION_MODELS = [
    "qwen3-vl-8b-instruct",
    "qwen3-vl-30b-a3b-instruct",
    "qwen3-vl-32b-instruct",
]
QWEN_MODEL_OPTIONS = [*TEXT_MODELS, *VISION_MODELS]


class GuaguaQwenMultimodalNode:
    CATEGORY = "Guagua🐸/LLM"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "task_mode": (TASK_MODE_OPTIONS, {"default": "text_chat"}),
                "model": (QWEN_MODEL_OPTIONS, {"default": "qwen-plus"}),
                "system_prompt": ("STRING", {"default": "You are a helpful assistant.", "multiline": True}),
                "user_prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image_path_or_url": ("STRING", {"default": "", "multiline": False}),
                "video_path_or_url": ("STRING", {"default": "", "multiline": False}),
            },
        }

    def run(
        self,
        api_key: str,
        task_mode: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        image=None,
        image_path_or_url: str = "",
        video_path_or_url: str = "",
    ):
        clean_user_prompt = ensure_text(user_prompt, "user_prompt")
        clean_system_prompt = system_prompt.strip()

        try:
            if task_mode == "text_chat":
                self._validate_model(task_mode, model)
                dashscope = configure_dashscope(api_key)
                messages = []
                if clean_system_prompt:
                    messages.append({"role": "system", "content": clean_system_prompt})
                messages.append({"role": "user", "content": clean_user_prompt})
                response = dashscope.Generation.call(
                    api_key=api_key.strip(),
                    model=model,
                    messages=messages,
                    result_format="message",
                )
                return (extract_text_response_content(response),)

            if task_mode == "image_analysis":
                self._validate_model(task_mode, model)
                dashscope = configure_dashscope(api_key)
                temp_file_path = None
                try:
                    image_reference, temp_file_path = self._resolve_image_reference(image, image_path_or_url)
                    messages = self._build_multimodal_messages(
                        clean_system_prompt,
                        {"image": image_reference},
                        clean_user_prompt,
                    )
                    response = dashscope.MultiModalConversation.call(
                        api_key=api_key.strip(),
                        model=model,
                        messages=messages,
                        result_format="message",
                    )
                    return (extract_text_response_content(response),)
                finally:
                    safe_remove_file(temp_file_path)

            if task_mode == "video_analysis":
                self._validate_model(task_mode, model)
                dashscope = configure_dashscope(api_key)
                video_reference = normalize_media_reference(video_path_or_url, "video_path_or_url")
                messages = self._build_multimodal_messages(
                    clean_system_prompt,
                    {"video": video_reference, "fps": 2.0},
                    clean_user_prompt,
                )
                response = dashscope.MultiModalConversation.call(
                    api_key=api_key.strip(),
                    model=model,
                    messages=messages,
                    result_format="message",
                )
                return (extract_text_response_content(response),)

            raise ValueError(f"Unsupported task_mode: {task_mode}")
        except Exception as exc:
            raise RuntimeError(format_api_exception("Qwen Multimodal", exc)) from exc

    def _validate_model(self, task_mode: str, model: str):
        if task_mode == "text_chat" and model not in TEXT_MODELS:
            raise ValueError(f"text_chat requires one of these models: {', '.join(TEXT_MODELS)}")
        if task_mode in {"image_analysis", "video_analysis"} and model not in VISION_MODELS:
            raise ValueError(
                f"{task_mode} requires one of these models: {', '.join(VISION_MODELS)}"
            )

    def _build_multimodal_messages(self, system_prompt: str, media_item: dict, user_prompt: str):
        messages = []
        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": [{"text": system_prompt}],
                }
            )
        messages.append(
            {
                "role": "user",
                "content": [media_item, {"text": user_prompt}],
            }
        )
        return messages

    def _resolve_image_reference(self, image, image_path_or_url: str) -> tuple[str, str | None]:
        if image is not None:
            temp_file_path = comfy_image_to_temp_file(image)
            return temp_file_path, temp_file_path

        return normalize_media_reference(image_path_or_url, "image_path_or_url"), None


NODE_CLASS_MAPPINGS = {
    "Qwen Multimodal": GuaguaQwenMultimodalNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen Multimodal": "Qwen Multimodal",
}
