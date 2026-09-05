"""Custom iOS-style bottom tab bar (5 tabs, icon + label).

Height: 56 dp of content + the device home-indicator inset added by
ft.SafeArea (on iPhone standalone PWA this totals ~80 dp).

`bottom_nav(selected, on_change)` keeps the legacy factory name and signature;
the only contract change is that `on_change` now receives the tab index (int)
instead of a ControlEvent — main.py was updated accordingly.
"""

import flet as ft

from theme import ACCENT, BG, BORDER, BOTTOM_NAV_CONTENT_HEIGHT, TEXT_SECONDARY

TABS = [
    (ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Сегодня"),
    (ft.Icons.FITNESS_CENTER_OUTLINED, ft.Icons.FITNESS_CENTER, "Тренировки"),
    (ft.Icons.RESTAURANT_OUTLINED, ft.Icons.RESTAURANT, "Питание"),
    (ft.Icons.MEDICATION_OUTLINED, ft.Icons.MEDICATION, "Протокол"),
    (ft.Icons.SHOW_CHART_OUTLINED, ft.Icons.SHOW_CHART, "Аналитика"),
]


def BottomNav(active_index: int, on_change) -> ft.Control:
    items = []
    for index, (icon, active_icon, label) in enumerate(TABS):
        active = index == active_index
        items.append(ft.Container(
            content=ft.Column([
                ft.Icon(
                    active_icon if active else icon,
                    size=24,
                    color=ACCENT if active else TEXT_SECONDARY,
                ),
                ft.Text(
                    label,
                    size=11,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                    color=ACCENT if active else TEXT_SECONDARY,
                ),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            expand=True,
            height=BOTTOM_NAV_CONTENT_HEIGHT,
            alignment=ft.Alignment.CENTER,
            on_click=lambda _, idx=index: on_change(idx),
            ink=True,
        ))
    return ft.SafeArea(
        avoid_intrusions_top=False,
        content=ft.Container(
            content=ft.Row(items, spacing=0),
            bgcolor=BG,
            border=ft.Border.only(top=ft.BorderSide(1, BORDER)),
        ),
    )


def bottom_nav(selected: int, on_change) -> ft.Control:
    """Legacy-compatible factory for the new iOS-style tab bar."""
    return BottomNav(selected, on_change)
