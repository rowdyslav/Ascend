"""Blocking loading overlay: semi-transparent scrim + centered spinner.

Pushed onto `page.overlay` it acts as a global "spinner over the screen" while
API calls are in flight.

NOTE: the app's ApiClient is synchronous (httpx), so a plain blocking
`api.get(...)` inside a handler freezes the event loop and the spinner won't
animate. Use it together with `page.run_task(...)` + `asyncio.to_thread(...)`
so the network call runs off the loop while the overlay keeps spinning.
"""

import flet as ft

from app.theme import ACCENT, TEXT_SECONDARY


class LoadingOverlay(ft.Container):
    def __init__(self, label: str = "Загрузка…"):
        super().__init__(
            content=ft.Column(
                [
                    ft.ProgressRing(width=48, height=48, stroke_width=4, color=ACCENT),
                    ft.Text(label, size=13, color=TEXT_SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                tight=True,
            ),
            bgcolor="#99000000",
            alignment=ft.Alignment.CENTER,
            left=0,
            top=0,
            right=0,
            bottom=0,
        )


def show_loading(page: ft.Page, label: str = "Загрузка…") -> LoadingOverlay:
    overlay = LoadingOverlay(label)
    page.overlay.append(overlay)
    page.update()
    return overlay


def hide_loading(page: ft.Page, overlay: LoadingOverlay) -> None:
    if overlay in page.overlay:
        page.overlay.remove(overlay)
    page.update()
