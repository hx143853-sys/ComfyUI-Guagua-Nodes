from __future__ import annotations

from ..style_library import get_style_preset, list_style_categories, list_style_labels


STYLE_CATEGORIES = list_style_categories()
STYLE_PRESET_OPTIONS = ["空", *list_style_labels()]


class GuaguaStylePromptPresetNode:
    CATEGORY = "Guagua🐸/Prompt"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build_prompt"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_prompt": ("STRING", {"default": "", "multiline": True}),
                "category": (STYLE_CATEGORIES, {"default": "空"}),
                "preset": (STYLE_PRESET_OPTIONS, {"default": "空"}),
            }
        }

    def build_prompt(self, base_prompt: str, category: str, preset: str):
        clean_base_prompt = base_prompt.strip()

        if category == "空" or preset == "空":
            return (clean_base_prompt,)

        preset_data = get_style_preset(category, preset)
        suffix = preset_data["prompt_suffix_en"].strip()
        if not clean_base_prompt:
            return (suffix,)
        return (f"{clean_base_prompt}, {suffix}",)


NODE_CLASS_MAPPINGS = {
    "Style Prompt Preset": GuaguaStylePromptPresetNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Style Prompt Preset": "Style Prompt Preset",
}
