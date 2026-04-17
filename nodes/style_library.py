from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


STYLE_LIBRARY_PATH = Path(__file__).with_name("data").joinpath("style_presets.json")


@lru_cache(maxsize=1)
def load_style_presets() -> list[dict]:
    with STYLE_LIBRARY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise RuntimeError("Style preset data must be a list.")
    return data


def get_style_preset(category_cn: str, label_cn: str) -> dict:
    for preset in load_style_presets():
        if preset["category_cn"] == category_cn and preset["label_cn"] == label_cn:
            return preset
    raise KeyError(f"Style preset not found for category '{category_cn}' and label '{label_cn}'.")


def list_style_labels() -> list[str]:
    return [preset["label_cn"] for preset in load_style_presets()]


def list_style_categories() -> list[str]:
    categories = ["空"]
    for preset in load_style_presets():
        category = preset["category_cn"]
        if category not in categories:
            categories.append(category)
    return categories
