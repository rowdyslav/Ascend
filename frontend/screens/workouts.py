import asyncio
from datetime import date

import flet as ft

from api_client import ApiClient, ApiError
from components.buttons import IconButton as AppIconButton
from components.buttons import PrimaryButton
from components.card import AppCard, section_title
from components.inputs import AppTextField
from components.loading import hide_loading, show_loading
from theme import COLORS, ERROR, SUCCESS, TEXT_SECONDARY


def workouts_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    root = ft.Column(expand=True)

    def notify(text: str, failed: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if failed else SUCCESS))

    def draw() -> None:
        overlay = show_loading(page, "Загрузка данных...")

        def _fetch_and_build():
            try:
                today = date.today().isoformat()
                week = api.get("/workouts/week", {"date": today})
                workout = next((item for item in week if item["date"] == today), None)
                exercises = api.get("/exercises")
            except ApiError as exc:
                return [ft.Text(str(exc), color=ERROR)]

            if workout is None:
                def create_workout(_: ft.ControlEvent) -> None:
                    try:
                        api.post("/workouts", {"date": today, "name": "Тренировка"})
                        draw()
                    except ApiError as exc:
                        notify(str(exc), True)

                return [ft.ListView(expand=True, padding=16, spacing=12, controls=[
                    AppCard(ft.Column([
                        ft.Text("Нет тренировки на сегодня", color=TEXT_SECONDARY),
                        PrimaryButton("Создать тренировку", on_click=create_workout, expand=True),
                    ], spacing=10, tight=True)),
                ])]

            return [ft.ListView(expand=True, padding=16, spacing=12, controls=[active_session(workout, exercises)])]

        async def _load():
            try:
                controls = await asyncio.to_thread(_fetch_and_build)
                root.controls.clear()
                root.controls.extend(controls)
            finally:
                hide_loading(page, overlay)
                page.update()

        page.run_task(_load)

    def last_session_text(exercise_id: str, workout_id: str) -> str | None:
        try:
            history = api.get(f"/exercises/{exercise_id}/history")
        except ApiError:
            return None
        previous = [item for item in history if item["workout_id"] != workout_id and item.get("workout_date")]
        if not previous:
            return None
        last_date = max(item["workout_date"] for item in previous)
        session_sets = sorted((item for item in previous if item["workout_date"] == last_date), key=lambda item: (item["order"], item["set_number"]))
        text = " · ".join(f"{item['weight_kg']:.0f}кг × {item['reps']}" for item in session_sets[-4:])
        return f"Прошлый ({last_date}): {text}"

    def active_session(workout: dict, exercises: list[dict]) -> ft.Control:
        try:
            current_sets = api.get(f"/workouts/{workout['id']}/sets")
        except ApiError:
            current_sets = []
        grouped: dict[str, list[dict]] = {}
        for item in current_sets:
            grouped.setdefault(item["exercise_id"], []).append(item)
        selected_exercise = ft.Dropdown(label="Упражнение", options=[ft.dropdown.Option(key=item["id"], text=item["name"]) for item in exercises], expand=True)
        weight = AppTextField("Вес, кг", keyboard_type=ft.KeyboardType.NUMBER)
        weight.width = 105
        reps = AppTextField("Повторы", keyboard_type=ft.KeyboardType.NUMBER)
        reps.width = 95
        rir = AppTextField("RIR", keyboard_type=ft.KeyboardType.NUMBER, value="2")
        rir.width = 70
        rest = AppTextField("Отдых, сек", keyboard_type=ft.KeyboardType.NUMBER, value="90")
        rest.width = 110
        last_hint = ft.Text("", size=12, color=TEXT_SECONDARY)
        expanded: dict[str, bool] = {}

        def exercise_by_id(exercise_id: str) -> dict:
            return next((item for item in exercises if item["id"] == exercise_id), {"name": "Упражнение"})

        def on_select(_: ft.ControlEvent) -> None:
            if selected_exercise.value:
                last_hint.value = last_session_text(selected_exercise.value, workout["id"]) or ""
                last_hint.update()
        selected_exercise.on_change = on_select

        def add_set(_: ft.ControlEvent) -> None:
            try:
                if not selected_exercise.value:
                    raise ValueError("Выберите упражнение")
                existing = grouped.get(selected_exercise.value, [])
                payload = {
                    "exercise_id": selected_exercise.value, "order": len(grouped), "set_number": len(existing) + 1,
                    "weight_kg": float(weight.value), "reps": int(reps.value),
                    "rir": int(rir.value) if rir.value else None, "rest_sec": int(rest.value) if rest.value else None,
                }
                api.post(f"/workouts/{workout['id']}/sets", payload)
                notify("Сет сохранён")
                draw()
            except (TypeError, ValueError, ApiError) as exc:
                notify(str(exc), True)

        def toggle_expand(exercise_id: str) -> None:
            expanded[exercise_id] = not expanded.get(exercise_id, True)
            draw()

        exercise_blocks = []
        for exercise_id in grouped:
            items = grouped[exercise_id]
            name = exercise_by_id(exercise_id)["name"]
            previous = last_session_text(exercise_id, workout["id"]) or "Прошлый: нет данных"
            is_open = expanded.get(exercise_id, True)
            header = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(name, weight=ft.FontWeight.W_600, size=15),
                        ft.Text(f"{len(items)} сетов", size=12, color=TEXT_SECONDARY),
                    ], expand=True, spacing=2),
                    AppIconButton(ft.Icons.KEYBOARD_ARROW_UP if is_open else ft.Icons.KEYBOARD_ARROW_DOWN, on_click=lambda _, value=exercise_id: toggle_expand(value), color=TEXT_SECONDARY, bg="transparent"),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=lambda _, value=exercise_id: toggle_expand(value), ink=True, border_radius=8,
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            )
            group_controls = [header]
            if is_open:
                group_controls.append(ft.Text(previous, size=12, color=TEXT_SECONDARY))
                for item in items:
                    group_controls.append(AppCard(ft.Row([
                        ft.Text(f"Сет {item['set_number']}", width=52, color=TEXT_SECONDARY, size=12),
                        ft.Text(f"{item['weight_kg']:.0f} кг × {item['reps']}", expand=True),
                    ]), padding=12))
            exercise_blocks.append(ft.Container(
                content=ft.Column(group_controls, spacing=8, tight=True),
                padding=12, border_radius=12, bgcolor=COLORS["bg_tertiary"],
            ))

        return AppCard(ft.Column([
            section_title(workout["name"]),
            *(exercise_blocks or [ft.Container(content=ft.Text("Добавьте первое упражнение", color=TEXT_SECONDARY), padding=6)]),
            ft.Divider(),
            ft.Text("Добавить сет", size=16, weight=ft.FontWeight.W_600),
            ft.Row([selected_exercise]),
            ft.Row([weight, reps], wrap=True),
            last_hint,
            ft.Row([rir, rest], wrap=True),
            PrimaryButton("Сет", icon=ft.Icons.ADD, on_click=add_set, expand=True),
        ], spacing=10, tight=True))

    draw()
    return root
