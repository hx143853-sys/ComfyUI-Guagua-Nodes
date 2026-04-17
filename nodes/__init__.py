from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

NODE_PREFIX = "Guagua🐸"
NODE_GROUPS = ("builtin", "custom")


def _with_prefix(name: str) -> str:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Node name cannot be empty.")
    if clean_name.startswith(NODE_PREFIX):
        return clean_name
    return f"{NODE_PREFIX} {clean_name}"


def _load_group_modules(group_name: str) -> list[ModuleType]:
    package_name = f"{__name__}.{group_name}"
    package = importlib.import_module(package_name)
    modules: list[ModuleType] = []

    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.ispkg or module_info.name.startswith("_"):
            continue
        modules.append(importlib.import_module(f"{package_name}.{module_info.name}"))

    return modules


def _collect_raw_nodes() -> tuple[dict[str, type], dict[str, str]]:
    raw_class_mappings: dict[str, type] = {}
    raw_display_mappings: dict[str, str] = {}

    for group_name in NODE_GROUPS:
        for module in _load_group_modules(group_name):
            module_class_mappings = getattr(module, "NODE_CLASS_MAPPINGS", {})
            module_display_mappings = getattr(module, "NODE_DISPLAY_NAME_MAPPINGS", {})

            duplicate_names = set(raw_class_mappings).intersection(module_class_mappings)
            if duplicate_names:
                duplicate_list = ", ".join(sorted(duplicate_names))
                raise ValueError(f"Duplicate node names found: {duplicate_list}")

            raw_class_mappings.update(module_class_mappings)
            raw_display_mappings.update(module_display_mappings)

    return raw_class_mappings, raw_display_mappings


RAW_NODE_CLASS_MAPPINGS, RAW_NODE_DISPLAY_NAME_MAPPINGS = _collect_raw_nodes()

NODE_CLASS_MAPPINGS = {
    _with_prefix(node_name): node_class
    for node_name, node_class in RAW_NODE_CLASS_MAPPINGS.items()
}

NODE_DISPLAY_NAME_MAPPINGS = {
    _with_prefix(node_name): _with_prefix(
        RAW_NODE_DISPLAY_NAME_MAPPINGS.get(node_name, node_name)
    )
    for node_name in RAW_NODE_CLASS_MAPPINGS
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "NODE_PREFIX",
]
