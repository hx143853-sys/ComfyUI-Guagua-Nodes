from __future__ import annotations


def _compact_parts(*parts: str, skip_empty: bool = True) -> list[str]:
    if skip_empty:
        return [part for part in parts if part]
    return list(parts)


class GuaguaTextJoinNode:
    CATEGORY = "Guagua🐸/Text"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "join_text"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_a": ("STRING", {"multiline": True, "default": ""}),
                "text_b": ("STRING", {"multiline": True, "default": ""}),
                "separator": ("STRING", {"default": ", "}),
                "skip_empty": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "text_c": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def join_text(
        self,
        text_a: str,
        text_b: str,
        separator: str,
        skip_empty: bool,
        text_c: str = "",
    ):
        parts = _compact_parts(text_a, text_b, text_c, skip_empty=skip_empty)
        return (separator.join(parts),)


class GuaguaPromptBuilderNode:
    CATEGORY = "Guagua🐸/Prompt"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build_prompt"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "subject": ("STRING", {"multiline": True, "default": ""}),
                "style": ("STRING", {"multiline": True, "default": ""}),
                "lighting": ("STRING", {"multiline": True, "default": ""}),
                "camera": ("STRING", {"multiline": True, "default": ""}),
                "extra": ("STRING", {"multiline": True, "default": ""}),
                "separator": ("STRING", {"default": ", "}),
            }
        }

    def build_prompt(
        self,
        subject: str,
        style: str,
        lighting: str,
        camera: str,
        extra: str,
        separator: str,
    ):
        parts = _compact_parts(subject, style, lighting, camera, extra)
        return (separator.join(parts),)


NODE_CLASS_MAPPINGS = {
    "Text Join": GuaguaTextJoinNode,
    "Prompt Builder": GuaguaPromptBuilderNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Join": "Text Join",
    "Prompt Builder": "Prompt Builder",
}
