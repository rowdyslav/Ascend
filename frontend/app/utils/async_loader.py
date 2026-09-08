"""Run a screen's blocking build (httpx fetches + control construction) off the
UI thread so the loading overlay can animate and the app stays responsive."""

import asyncio
from collections.abc import Callable

import flet as ft

from app.components.loading import hide_loading, show_loading
from app.theme import ERROR
from app.utils.logger import logger


def load_screen(page: ft.Page, build_fn: Callable[[], list[ft.Control]], root) -> None:
    """Build controls via `build_fn` in a worker thread and attach them to `root`.

    `root` must be a control exposing a mutable `.controls` list (Column,
    ListView, Row, ...). Any exception is surfaced as a friendly error text so a
    malformed API response can never crash the session.
    """
    overlay = show_loading(page, "Загрузка...")

    async def _load() -> None:
        try:
            try:
                controls = await asyncio.to_thread(build_fn)
            except Exception as exc:
                logger.exception("Screen load failed: %s", exc)
                controls = [ft.Text(f"Ошибка загрузки: {exc}", color=ERROR)]
            root.controls.clear()
            root.controls.extend(controls)
        finally:
            hide_loading(page, overlay)
            page.update()

    page.run_task(_load)
