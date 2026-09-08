"""Native iOS-style bottom sheet helper (drag handle, 24 dp top corners).

Uses the same modal mechanism as the legacy screens (page.show_dialog) so it
behaves identically everywhere. ft.BottomSheet applies the safe area itself
(use_safe_area=True by default), so the home-indicator inset is handled by
Flet on iPhone standalone PWA.
"""

import flet as ft

from app.theme import COLORS, RADII, TEXT_DISABLED


def show_bottom_sheet(page: ft.Page, content: ft.Control, is_dismissible: bool = True) -> None:
    sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                # Drag handle
                ft.Container(
                    width=40,
                    height=4,
                    bgcolor=TEXT_DISABLED,
                    border_radius=999,
                    margin=ft.Margin.only(top=8, bottom=16),
                ),
                content,
            ], tight=True, spacing=0),
            bgcolor=COLORS["bg_elevated"],
            border_radius=ft.BorderRadius.only(top_left=RADII["xl"], top_right=RADII["xl"]),
            padding=ft.Padding.only(left=16, right=16, bottom=16),
        ),
        show_drag_handle=False,
        draggable=True,
        dismissible=is_dismissible,
    )
    page.show_dialog(sheet)
