"""Shared default categorical palette for alternatives and criteria.

Eight hues ordered for maximum adjacent colorblind-safe separation. Used as
the fallback whenever an alternative or criterion has no user-assigned
color; any color set explicitly on the model always takes precedence.
"""
from __future__ import annotations

DEFAULT_PALETTE: list[str] = [
    "#2a78d6",  # blue
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
    "#e87ba4",  # magenta
    "#eb6834",  # orange
]


def default_color(index: int) -> str:
    return DEFAULT_PALETTE[index % len(DEFAULT_PALETTE)]
