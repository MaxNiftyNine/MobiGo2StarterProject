#!/usr/bin/env python3
"""Validate and emit the host-side .HBI launcher metadata companion."""

from __future__ import annotations

import json
from pathlib import Path


TITLE_BYTES = 18
DESCRIPTION_BYTES = 22
AUTHOR_BYTES = 10
ICON_NAMES = ("default", "game", "puzzle", "media", "tool", "system")


def validate_text(value: object, field: str, size: int, *, required: bool) -> str:
    if not isinstance(value, str):
        raise ValueError(f"homebrew.{field} must be a string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"homebrew.{field} must contain ASCII characters") from error
    if (required and not encoded) or len(encoded) >= size:
        raise ValueError(
            f"homebrew.{field} must be at most {size - 1} ASCII bytes"
        )
    return value


def normalize(value: object, *, fallback_title: str) -> dict[str, object]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("homebrew must be an object")
    unknown = sorted(set(value) - {"title", "description", "author", "icon"})
    if unknown:
        raise ValueError(f"unknown homebrew field: {unknown[0]}")
    icon = value.get("icon", "default")
    if not isinstance(icon, str) or icon.lower() not in ICON_NAMES:
        raise ValueError(f"homebrew.icon must be one of: {', '.join(ICON_NAMES)}")
    return {
        "schema": 1,
        "title": validate_text(
            value.get("title", fallback_title), "title", TITLE_BYTES, required=True
        ),
        "description": validate_text(
            value.get("description", ""),
            "description",
            DESCRIPTION_BYTES,
            required=False,
        ),
        "author": validate_text(
            value.get("author", ""), "author", AUTHOR_BYTES, required=False
        ),
        "icon": icon.lower(),
    }


def write(path: Path, metadata: dict[str, object]) -> None:
    path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
