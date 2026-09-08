"""iOS-style form controls: text field (52 dp) and large touch-friendly checkbox."""

import flet as ft

from app.theme import ACCENT, BORDER, COLORS, TEXT, TEXT_SECONDARY, TOUCH_TARGET


def AppTextField(label: str, value: str = "", keyboard_type=None, hint: str = "",
                 on_change=None, on_submit=None, autofocus: bool = False) -> ft.TextField:
    """Fixed-height (52 dp) iOS-style text field. Never expands — keeps layouts
    stable when the on-screen keyboard appears."""
    return ft.TextField(
        label=label,
        value=value,
        hint_text=hint,
        keyboard_type=keyboard_type,
        on_change=on_change,
        on_submit=on_submit,
        autofocus=autofocus,
        border_color=BORDER,
        focused_border_color=ACCENT,
        cursor_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=13),
        text_size=16,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        border_radius=12,
        bgcolor=COLORS["bg_tertiary"],
        height=52,
    )


def AppCheckbox(value: bool, on_change, label: str = "") -> ft.Container:
    """28x28 custom checkbox with a 48 dp tap area (whole row is tappable).
    Self-contained: toggles its own visuals and reports the new value."""
    state = {"value": bool(value)}
    icon = ft.Icon(
        ft.Icons.CHECK, size=18,
        color=COLORS["bg_primary"] if state["value"] else "transparent",
    )
    box = ft.Container(
        content=icon,
        width=28,
        height=28,
        border_radius=8,
        bgcolor=ACCENT if state["value"] else "transparent",
        border=ft.Border.all(2, ACCENT if state["value"] else BORDER),
        animate_scale=100,
    )

    def toggle(_) -> None:
        state["value"] = not state["value"]
        box.bgcolor = ACCENT if state["value"] else "transparent"
        box.border = ft.Border.all(2, ACCENT if state["value"] else BORDER)
        icon.color = COLORS["bg_primary"] if state["value"] else "transparent"
        box.update()
        on_change(state["value"])

    row = ft.Row(
        [box, ft.Text(label, size=15, color=TEXT) if label else None],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        content=row,
        on_click=toggle,
        height=TOUCH_TARGET,
        padding=ft.Padding.symmetric(vertical=6),
        alignment=ft.Alignment.CENTER_LEFT,
    )
