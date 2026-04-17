from __future__ import annotations

from ..api_utils import (
    create_ark_client,
    download_image_as_tensor,
    extract_first_image_url,
    format_api_exception,
)


SEEDREAM_MODELS = [
    "doubao-seedream-5-0-lite-260128",
    "doubao-seedream-5-0-260128",
]

SEEDREAM_SIZE_PRESETS = [
    "adaptive",
    "1:1",
    "4:3",
    "3:4",
    "16:9",
    "9:16",
    "3:2",
    "2:3",
]


class GuaguaSeedreamImageNode:
    CATEGORY = "Guagua🐸/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "model": (SEEDREAM_MODELS, {"default": SEEDREAM_MODELS[0]}),
                "size_preset": (SEEDREAM_SIZE_PRESETS, {"default": "adaptive"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "guidance_scale": ("FLOAT", {"default": 2.5, "min": 0.0, "max": 20.0, "step": 0.1}),
                "watermark": ("BOOLEAN", {"default": True}),
            }
        }

    def generate_image(
        self,
        api_key: str,
        prompt: str,
        model: str,
        size_preset: str,
        seed: int,
        guidance_scale: float,
        watermark: bool,
    ):
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("prompt cannot be empty.")

        try:
            client = create_ark_client(api_key)
            request_payload = {
                "model": model,
                "prompt": clean_prompt,
                "size": size_preset,
                "n": 1,
                "guidance_scale": float(guidance_scale),
                "watermark": bool(watermark),
                "response_format": "url",
            }
            if seed > 0:
                request_payload["seed"] = int(seed)

            response = client.images.generate(**request_payload)
            image_url = extract_first_image_url(response)
            if not image_url:
                raise RuntimeError("Seedream returned no image URL.")

            return (download_image_as_tensor(image_url),)
        except Exception as exc:
            raise RuntimeError(format_api_exception("Seedream 5.0", exc)) from exc


NODE_CLASS_MAPPINGS = {
    "Seedream 5.0 Image": GuaguaSeedreamImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream 5.0 Image": "Seedream 5.0 Image",
}
