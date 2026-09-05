"""Chip badge with 12% tinted background by default."""

import flet as ft

from theme import ACCENT


def Chip(text: str, color: str = ACCENT, bg: str | None = None) -> ft.Container:
    if bg is None:
        bg = color + "20"  # 12% opacity of the accent colour
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color),
        bgcolor=bg,
        border_radius=999,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )
