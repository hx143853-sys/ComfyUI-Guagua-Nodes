from __future__ import annotations

from ..api_utils import (
    comfy_image_to_data_uris,
    create_ark_client,
    download_image_as_tensor,
    extract_first_image_url,
    format_api_exception,
)


SEEDREAM_MODELS = [
    "doubao-seedream-5-0-lite-260128",
    "doubao-seedream-5-0-260128",
]

SEEDREAM_RESOLUTION_PRESETS = ["2K", "3K"]
SEEDREAM_ASPECT_RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
SEEDREAM_OUTPUT_FORMATS = ["png", "jpeg"]
SEEDREAM_MAX_REFERENCE_IMAGES = 10


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
                "resolution": (SEEDREAM_RESOLUTION_PRESETS, {"default": "2K"}),
                "aspect_ratio": (SEEDREAM_ASPECT_RATIOS, {"default": "1:1"}),
                "output_format": (SEEDREAM_OUTPUT_FORMATS, {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "guidance_scale": ("FLOAT", {"default": 2.5, "min": 0.0, "max": 20.0, "step": 0.1}),
                "watermark": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "image": ("IMAGE",),
            }
        }

    def generate_image(
        self,
        api_key: str,
        prompt: str,
        model: str,
        resolution: str,
        aspect_ratio: str,
        output_format: str,
        seed: int,
        guidance_scale: float,
        watermark: bool,
        image=None,
    ):
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("prompt cannot be empty.")

        try:
            client = create_ark_client(api_key)
            request_payload = {
                "model": model,
                "prompt": clean_prompt,
                "size": resolution,
                "watermark": bool(watermark),
                "output_format": output_format,
            }
            if image is not None:
                image_payload = self._prepare_reference_images(image)
                request_payload["image"] = image_payload
                if isinstance(image_payload, list):
                    request_payload["sequential_image_generation"] = "disabled"

            response = client.images.generate(**request_payload)
            image_url = extract_first_image_url(response)
            if not image_url:
                raise RuntimeError("Seedream returned no image URL.")

            return (download_image_as_tensor(image_url),)
        except Exception as exc:
            raise RuntimeError(format_api_exception("Seedream 5.0", exc)) from exc

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


NODE_CLASS_MAPPINGS = {
    "Seedream 5.0 Image": GuaguaSeedreamImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream 5.0 Image": "Seedream 5.0 Image",
}
