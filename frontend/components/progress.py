"""Progress indicators.

The horizontal bar is implemented with ft.ProgressBar (same visual spec as a
hand-built Container track, but layout-safe: native width/height behaviour
inside Columns/Rows and animated value transitions).

`over_color` controls the colour once the bar reaches 100%. The design-system
default is ERROR (the prompt spec); callers where hitting 100% is the goal pass
over_color=ACCENT so a completed bar stays positive.
"""

import flet as ft

from theme import ACCENT, COLORS, ERROR


def ProgressBar(value: float, max_value: float = 100, color: str = ACCENT,
                height: int = 6, over_color: str | None = None) -> ft.ProgressBar:
    pct = min(1.0, max(0.0, value / max_value)) if max_value else 0.0
    fill = color if pct < 1.0 else (over_color if over_color is not None else ERROR)
    return ft.ProgressBar(
        value=pct,
        color=fill,
        bgcolor=COLORS["progress_bg"],
        bar_height=height,
        border_radius=999,
    )
