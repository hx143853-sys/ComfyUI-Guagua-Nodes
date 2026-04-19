from __future__ import annotations

import time

from ..api_utils import (
    comfy_image_to_data_uris,
    download_image_as_tensor,
    extract_first_image_url,
    format_api_exception,
    post_ark_json,
)


SEEDREAM_RESOLUTION_PRESETS = ["2K", "3K"]
SEEDREAM_ASPECT_RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
SEEDREAM_OUTPUT_FORMATS = ["png", "jpeg"]
SEEDREAM_MAX_REFERENCE_IMAGES = 10
SEEDREAM_MAX_RETRIES = 3
SEEDREAM_RETRY_DELAY_SECONDS = 2.0
SEEDREAM_50_LITE_MODELS = [
    "doubao-seedream-5-0-lite-260128",
    "doubao-seedream-5-0-260128",
]
SEEDREAM_45_MODEL = "doubao-seedream-4-5-251128"
SEEDREAM_45_MODELS = [
    "doubao-seedream-4-5-251128",
]
SEEDREAM_OUTPUT_FORMAT_MODELS = {
    "doubao-seedream-5-0-lite-260128",
    "doubao-seedream-5-0-260128",
}
SEEDREAM_SIZE_MAP = {
    "2K": {
        "1:1": "2048x2048",
        "4:3": "2304x1728",
        "3:4": "1728x2304",
        "16:9": "2848x1600",
        "9:16": "1600x2848",
        "3:2": "2496x1664",
        "2:3": "1664x2496",
        "21:9": "3136x1344",
    },
    "3K": {
        "1:1": "3072x3072",
        "4:3": "3456x2592",
        "3:4": "2592x3456",
        "16:9": "4096x2304",
        "9:16": "2304x4096",
        "3:2": "3744x2496",
        "2:3": "2496x3744",
        "21:9": "4704x2016",
    },
}


class _BaseGuaguaSeedreamImageNode:
    CATEGORY = "Guagua🐸/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"
    FIXED_MODEL: str | None = None
    MODEL_OPTIONS: list[str] | None = None

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "api_key": ("STRING", {"default": "", "multiline": False}),
            "prompt": ("STRING", {"default": "", "multiline": True}),
            "resolution": (SEEDREAM_RESOLUTION_PRESETS, {"default": "2K"}),
            "aspect_ratio": (SEEDREAM_ASPECT_RATIOS, {"default": "1:1"}),
            "output_format": (SEEDREAM_OUTPUT_FORMATS, {"default": "png"}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            "guidance_scale": ("FLOAT", {"default": 2.5, "min": 0.0, "max": 20.0, "step": 0.1}),
            "watermark": ("BOOLEAN", {"default": True}),
        }
        if cls.FIXED_MODEL is None and cls.MODEL_OPTIONS:
            required["model"] = (cls.MODEL_OPTIONS, {"default": cls.MODEL_OPTIONS[0]})
        return {
            "required": required,
            "optional": {
                "image": ("IMAGE",),
            }
        }

    def generate_image(
        self,
        api_key: str,
        prompt: str,
        resolution: str,
        aspect_ratio: str,
        output_format: str,
        seed: int,
        guidance_scale: float,
        watermark: bool,
        image=None,
        model: str | None = None,
    ):
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("prompt cannot be empty.")
        resolved_model = self.FIXED_MODEL or model
        if not resolved_model:
            raise ValueError("model cannot be empty.")
        resolved_size = self._resolve_size(resolution, aspect_ratio, resolved_model)

        request_payload = {
            "model": resolved_model,
            "prompt": clean_prompt,
            "size": resolved_size,
            "watermark": bool(watermark),
        }
        if resolved_model in SEEDREAM_OUTPUT_FORMAT_MODELS:
            request_payload["output_format"] = output_format
        if image is not None:
            image_payload = self._prepare_reference_images(image)
            request_payload["image"] = image_payload
            if isinstance(image_payload, list):
                request_payload["sequential_image_generation"] = "disabled"

        last_exception = None
        for attempt in range(1, SEEDREAM_MAX_RETRIES + 1):
            try:
                response = post_ark_json(api_key, "images/generations", request_payload)
                image_url = extract_first_image_url(response)
                if not image_url:
                    raise RuntimeError("Seedream returned no image URL.")
                return (download_image_as_tensor(image_url),)
            except Exception as exc:
                last_exception = exc
                adapted_payload = self._adapt_payload_for_exception(request_payload, exc)
                if adapted_payload is not None:
                    request_payload = adapted_payload
                    continue
                if attempt < SEEDREAM_MAX_RETRIES and self._is_retryable_exception(exc):
                    time.sleep(SEEDREAM_RETRY_DELAY_SECONDS)
                    continue
                raise RuntimeError(format_api_exception("Seedream 5.0", exc)) from exc

        raise RuntimeError(format_api_exception("Seedream 5.0", last_exception or RuntimeError("Unknown error")))

    def _prepare_reference_images(self, image) -> str | list[str]:
        image_references = comfy_image_to_data_uris(image, "PNG")
        if not image_references:
            raise ValueError("Connected IMAGE input did not contain any frames.")
        if len(image_references) > SEEDREAM_MAX_REFERENCE_IMAGES:
            raise ValueError(
                f"Seedream 5.0 currently supports at most {SEEDREAM_MAX_REFERENCE_IMAGES} reference images per request."
            )
        if len(image_references) == 1:
            return image_references[0]
        return image_references

    def _resolve_size(self, resolution: str, aspect_ratio: str, model: str) -> str:
        if model == SEEDREAM_45_MODEL:
            return resolution

        try:
            return SEEDREAM_SIZE_MAP[resolution][aspect_ratio]
        except KeyError as exc:
            raise ValueError(f"Unsupported Seedream size combination: {resolution} / {aspect_ratio}") from exc

    def _is_retryable_exception(self, exc: Exception) -> bool:
        message = (str(exc).strip() or exc.__class__.__name__).lower()
        return (
            "connection error" in message
            or "timed out" in message
            or "timeout" in message
            or "connection reset" in message
        )

    def _adapt_payload_for_exception(self, payload: dict, exc: Exception) -> dict | None:
        message = (str(exc).strip() or exc.__class__.__name__).lower()

        if "`output_format`" in message and "not supported" in message and "output_format" in payload:
            adapted = dict(payload)
            adapted.pop("output_format", None)
            return adapted

        if (
            "`sequential_image_generation`" in message
            and "not supported" in message
            and "sequential_image_generation" in payload
        ):
            adapted = dict(payload)
            adapted.pop("sequential_image_generation", None)
            return adapted

        return None


class GuaguaSeedream50LiteImageNode(_BaseGuaguaSeedreamImageNode):
    MODEL_OPTIONS = SEEDREAM_50_LITE_MODELS


class GuaguaSeedream45ImageNode(_BaseGuaguaSeedreamImageNode):
    FIXED_MODEL = SEEDREAM_45_MODEL


NODE_CLASS_MAPPINGS = {
    "Seedream 5.0 / Lite Image": GuaguaSeedream50LiteImageNode,
    "Seedream 4.5 Image": GuaguaSeedream45ImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream 5.0 / Lite Image": "Seedream 5.0 / Lite Image",
    "Seedream 4.5 Image": "Seedream 4.5 Image",
}
