"""iOS-style buttons: filled primary, ghost secondary, round icon button.

Material 3 is the rendering base (per project decision); ripple is the built-in
tap feedback. On top of it we add an iOS-style opacity press (dim to 0.7 on
tap, restore after a short delay) plus a desktop hover dim. Buttons take
`content=` (not `text=`), and the unified ft.Button is used for the primary
style.
"""

import asyncio

import flet as ft

from app.theme import ACCENT, BORDER, COLORS, TEXT

RADII_MD = 12  # buttons and inputs
PRESS_OPACITY = 0.7
HOVER_OPACITY = 0.85
RESTORE_DELAY = 0.12

# См. frontend/COMPAT.md: RoundedRectangleBorder radius keyword


def _btn_shape() -> ft.RoundedRectangleBorder:
    return ft.RoundedRectangleBorder(radius=RADII_MD)


def _page_or_none(control: ft.Control):
    try:
        return control.page
    except RuntimeError:
        return None


def _safe_update(control: ft.Control) -> None:
    """Update a control that may already be detached (never raise here)."""
    try:
        control.update()
    except RuntimeError:
        pass


def _pressable(button: ft.Control, on_click) -> ft.Control:
    """Wire opacity press feedback + desktop hover onto any button control."""

    def press(e: ft.ControlEvent) -> None:
        button.opacity = PRESS_OPACITY
        _safe_update(button)

        async def restore() -> None:
            await asyncio.sleep(RESTORE_DELAY)
            button.opacity = 1.0
            _safe_update(button)

        page = _page_or_none(button)
        if page is not None:
            page.run_task(restore)
        else:
            button.opacity = 1.0
        if on_click is not None:
            on_click(e)

    def hover(e: ft.ControlEvent) -> None:
        button.opacity = HOVER_OPACITY if e.data == "true" else 1.0
        _safe_update(button)

    button.on_click = press
    button.on_hover = hover
    button.animate_opacity = 200
    return button


def PrimaryButton(text: str, on_click, expand: bool = False, icon: str | None = None,
                  height: int = 52, disabled: bool = False) -> ft.Button:
    button = ft.Button(
        content=text,
        icon=icon,
        expand=expand,
        height=height,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor=ACCENT,
            color=COLORS["bg_primary"],
            shape=_btn_shape(),
            text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
            padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        ),
    )
    return _pressable(button, on_click)


def SecondaryButton(text: str, on_click, icon: str | None = None,
                    expand: bool = False, height: int = 48) -> ft.OutlinedButton:
    button = ft.OutlinedButton(
        content=text,
        icon=icon,
        expand=expand,
        height=height,
        style=ft.ButtonStyle(
            color=TEXT,
            side=ft.BorderSide(1, BORDER),
            shape=_btn_shape(),
            text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_500),
            padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        ),
    )
    return _pressable(button, on_click)


def IconButton(icon: str, on_click, size: int = 44, bg: str = COLORS["bg_tertiary"],
               color: str = TEXT, icon_size: int = 20) -> ft.IconButton:
    """Round icon button; 44 dp default matches the Apple HIG minimum."""
    button = ft.IconButton(
        icon=icon,
        icon_size=icon_size,
        icon_color=color,
        width=size,
        height=size,
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            bgcolor=bg,
            padding=0,
        ),
    )
    return _pressable(button, on_click)


# Non-shadowing alias for imports next to ft.IconButton.
AppIconButton = IconButton
