"""Screen scaffold (app bar + scrollable body + floating nav) and MetricCard.

// TODO [VISUAL]: legacy screens build their own roots (they existed before the
design system) and keep working unchanged; ScreenScaffold is available for new
screens and future migrations without touching the working layouts.
"""

import flet as ft

from components.bottom_nav import BottomNav
from components.buttons import IconButton
from components.card import AppCard
from theme import ACCENT, BG, COLORS, SUCCESS, ERROR, TEXT_SECONDARY


def ScreenScaffold(app_bar_title: str, content: ft.Control, bottom_nav_index: int,
                   on_nav_change, floating_action: ft.Control | None = None,
                   on_settings=None) -> ft.Stack:
    app_bar = ft.Container(
        content=ft.Row([
            ft.Text(app_bar_title, size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            ft.Container(expand=True),
            IconButton(ft.Icons.SETTINGS_OUTLINED, on_click=on_settings or (lambda _: None),
                       bg="transparent", color=TEXT_SECONDARY),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.only(left=16, right=16, top=8, bottom=12),
    )
    return ft.Stack([
        ft.Container(
            content=ft.Column([
                app_bar,
                ft.Container(
                    content=content,
                    expand=True,
                    padding=ft.Padding.only(left=16, right=16, top=8, bottom=88),
                ),
            ], spacing=0, tight=True),
            expand=True,
            bgcolor=BG,
        ),
        ft.Container(content=BottomNav(bottom_nav_index, on_nav_change), bottom=0, left=0, right=0),
        floating_action if floating_action else ft.Container(),
    ], expand=True)


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
