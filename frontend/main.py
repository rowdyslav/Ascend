import flet as ft

from api_client import ApiClient
from components.bottom_nav import bottom_nav
from screens.analytics import analytics_screen
from screens.nutrition import nutrition_screen
from screens.protocol import protocol_screen
from screens.today import today_screen
from screens.workouts import workouts_screen
from theme import apply_theme

SCREENS = [today_screen, workouts_screen, nutrition_screen, protocol_screen, analytics_screen]


def main(page: ft.Page) -> None:
    apply_theme(page)
    if not page.web:
        page.window.width = 420
        page.window.height = 860
    api = ApiClient()
    index = 0

    body = ft.Container(expand=True)
    nav_slot = ft.Container()

    def navigate(target: int) -> None:
        nonlocal index
        index = target
        body.content = SCREENS[target](page, api, navigate)
        nav_slot.content = bottom_nav(target, navigate)
        body.update()
        nav_slot.update()
        page.update()

    nav_slot.content = bottom_nav(index, navigate)
    body.content = SCREENS[0](page, api, navigate)
    page.add(ft.Column([body, nav_slot], expand=True, spacing=0))


if __name__ == "__main__":
    ft.run(main)
