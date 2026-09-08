"""Design-system primitives: MetricCard."""

import flet as ft

from app.components.card import AppCard
from app.theme import ACCENT, COLORS, ERROR, SUCCESS, TEXT_SECONDARY


def MetricCard(title: str, value: str, unit: str = "", delta: str | None = None,
               icon: str | None = None, color: str = ACCENT, width: int = 120,
               height: int = 100, onTap=None) -> ft.Container:
    delta_color = SUCCESS if delta and delta.startswith("+") else ERROR if delta and delta.startswith("-") else TEXT_SECONDARY
    return AppCard(
        ft.Column([
            ft.Row([
                ft.Icon(icon, size=18, color=color) if icon else None,
                ft.Text(title, size=13, color=TEXT_SECONDARY),
            ], spacing=8),
            ft.Row([
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                ft.Text(unit, size=14, color=TEXT_SECONDARY) if unit else None,
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.END),
            ft.Text(delta, size=12, color=delta_color) if delta else None,
        ], spacing=8, tight=True),
        padding=16,
        onTap=onTap,
        width=width,
        height=height,
    )
