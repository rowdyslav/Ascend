"""Shared snackbar helper — replaces the per-screen notify()/message() copies."""

import flet as ft

from app.theme import ERROR, SUCCESS


def show_snack(page: ft.Page, text: str, error: bool = False) -> None:
    page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if error else SUCCESS))
