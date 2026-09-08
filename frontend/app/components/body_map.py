from datetime import date
from typing import Callable

import flet as ft

from app.theme import MUTED, SUCCESS, TEXT, TEXT_SECONDARY, WARNING

ZONES = ["дельта Л", "дельта П", "бицепс Л", "бицепс П", "квад Л", "квад П", "ягодица Л", "ягодица П", "живот", "бедро Л", "бедро П", "живот низ"]


class BodyMap(ft.Column):
    """Grid of injection zones coloured by how long ago each one was used."""

    def __init__(self, last_use: dict[str, str | None], on_zone: Callable[[str], None]):
        tiles = []
        for zone in ZONES:
            last = last_use.get(zone)
            if not last:
                color, subtitle = MUTED, "не было"
            else:
                age = (date.today() - date.fromisoformat(last)).days
                color = SUCCESS if age < 7 else WARNING
                subtitle = f"{last} · {age} дн."
            tiles.append(ft.Container(
                content=ft.Column([
                    ft.Text(zone, size=12, text_align=ft.TextAlign.CENTER, color=TEXT),
                    ft.Text(subtitle, size=10, text_align=ft.TextAlign.CENTER, color=TEXT_SECONDARY),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=color + "33", border=ft.Border.all(1, color), border_radius=12, padding=10, width=112,
                on_click=lambda e, name=zone: on_zone(name), ink=True,
            ))
        super().__init__([
            ft.Text("Карта зон", size=17, weight=ft.FontWeight.W_600),
            ft.Row(tiles[:2], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(tiles[2:4], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(tiles[4:6], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(tiles[6:8], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(tiles[8:10], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(tiles[10:], alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
