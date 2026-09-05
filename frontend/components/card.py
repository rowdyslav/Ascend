import flet as ft

from theme import COLORS, RADIUS, SURFACE


def card(*controls: ft.Control, padding: int = 16, on_click=None, color: str = SURFACE) -> ft.Container:
    return ft.Container(
        content=ft.Column(list(controls), spacing=10, tight=True), padding=padding,
        border_radius=RADIUS, bgcolor=color, on_click=on_click,
        ink=on_click is not None,
    )


def section_title(title: str, action: ft.Control | None = None) -> ft.Row:
    controls = [ft.Text(title, size=18, weight=ft.FontWeight.W_600, expand=True)]
    if action:
        controls.append(action)
    return ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def AppCard(content: ft.Control, padding: int = 16, onTap=None,
            width: int | None = None, height: int | None = None) -> ft.Container:
    """Design-system card: bg_secondary, 16 dp radius, ripple on tap."""
    return ft.Container(
        content=content,
        bgcolor=COLORS["bg_secondary"],
        border_radius=RADIUS,
        padding=padding,
        width=width,
        height=height,
        margin=ft.Margin.only(bottom=12),
        on_click=onTap,
        animate_opacity=200,
        ink=onTap is not None,
    )
