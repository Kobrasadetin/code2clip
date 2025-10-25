from __future__ import annotations
from typing import Set

from extension_sets import TOP_CATEGORIES, EXTENSION_SETS
from extension_filters import parse_extensions


def compute_extension_filters(settings) -> list[str]:
    """Build the final extension allow-list from the new settings structure."""
    mode = getattr(settings, "extension_mode", "categories") or "categories"

    if mode == "allow_all":
        return []

    if mode == "custom":
        allowed = set(parse_extensions(getattr(settings, "custom_extensions_text", "")))
    else:
        allowed: Set[str] = set()

        if getattr(settings, "include_text", True):
            for subset in TOP_CATEGORIES.get("Text", []):
                allowed.update(EXTENSION_SETS.get(subset, []))

        if getattr(settings, "include_data", True):
            for subset in TOP_CATEGORIES.get("Data", []):
                allowed.update(EXTENSION_SETS.get(subset, []))

        if getattr(settings, "include_code", True):
            for subset in TOP_CATEGORIES.get("Code", []):
                allowed.update(EXTENSION_SETS.get(subset, []))

        excluded = getattr(settings, "excluded_subsets", {}) or {}
        for category, subset_list in excluded.items():
            for subset in subset_list or []:
                allowed.difference_update(EXTENSION_SETS.get(subset, []))

    denied = set(parse_extensions(getattr(settings, "excluded_extensions_text", "")))
    allowed.difference_update(denied)

    return sorted(allowed)
