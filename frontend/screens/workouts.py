import asyncio
from datetime import date, timedelta

import flet as ft

from api_client import ApiClient, ApiError
from components.buttons import IconButton as AppIconButton
from components.buttons import PrimaryButton, SecondaryButton
from components.card import AppCard, section_title
from components.chips import Chip
from components.circular_progress import CircularProgress
from components.inputs import AppCheckbox, AppTextField
from components.loading import hide_loading, show_loading
from components.sheets import show_bottom_sheet
from theme import ACCENT, COLORS, ERROR, SUCCESS, SURFACE, TEXT_SECONDARY

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# AppCheckbox is self-contained (it toggles its own visuals and reports the new
# state through on_change), so the screen keeps a mirrored dict of flag values
# that can be read at save time and set programmatically ("copy last set",
# "drop-set") — then the checkbox row is rebuilt so the visuals follow.
FLAG_DEFS = [("warmup", "Разминка"), ("failure", "Отказ"), ("dropset", "Дроп"), ("superset", "Суперсет")]


def workouts_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    selected_date = date.today()
    root = ft.Column(expand=True)
    # Persistent across redraws: draw() rebuilds the session card, so keeping
    # the ring/label at screen scope lets the running rest timer keep updating
    # the controls that are actually on screen.
    ring = CircularProgress(value=0, size=42, stroke=6, gradient=True, label="")
    rest_label = ft.Text("Отдых: готов", color=TEXT_SECONDARY)

    def notify(text: str, failed: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if failed else SUCCESS))

    def draw() -> None:
        # Show the loader immediately, run the blocking httpx fetch + control
        # build in a worker thread, then attach the result on the main loop.
        overlay = show_loading(page, "Загрузка данных...")

        def _fetch_and_build():
            try:
                monday = selected_date - timedelta(days=selected_date.weekday())
                week = api.get("/workouts/week", {"date": selected_date.isoformat()})
                by_date = {item["date"]: item for item in week}
                exercises = api.get("/exercises")
            except ApiError as exc:
                return [ft.Text(str(exc), color=ERROR)]

            day_buttons = []
            for offset in range(7):
                item_date = monday + timedelta(days=offset)
                active = item_date == selected_date
                workout = by_date.get(item_date.isoformat())
                icon = ft.Icons.CHECK if workout and workout.get("completed") else ft.Icons.HOTEL if workout and workout.get("is_rest_day") else ft.Icons.FITNESS_CENTER if workout else ft.Icons.ADD
                day_buttons.append(ft.Container(content=ft.Column([ft.Text(WEEKDAYS[offset], size=12), ft.Text(str(item_date.day), weight=ft.FontWeight.BOLD), ft.Icon(icon, size=15)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True), bgcolor=ACCENT + "33" if active else SURFACE, border_radius=12, padding=9, width=50, on_click=lambda e, value=item_date: select_date(value), ink=True))
            planner = ft.ListView(expand=True, spacing=12, padding=16)
            planner.controls.extend([
                section_title("Неделя", ft.Text(selected_date.strftime("%B %Y"), color=TEXT_SECONDARY)),
                ft.Row(day_buttons, scroll=ft.ScrollMode.AUTO),
            ])
            selected = by_date.get(selected_date.isoformat())

            def create_from_template(name: str, rest: bool = False) -> None:
                try:
                    api.post("/workouts", {"date": selected_date.isoformat(), "name": name, "is_rest_day": rest})
                    draw()
                except ApiError as exc:
                    notify(str(exc), True)

            def copy_last_week(_: ft.ControlEvent) -> None:
                previous_monday = monday - timedelta(days=7)
                try:
                    source = api.get("/workouts/week", {"date": previous_monday.isoformat()})
                    copied = 0
                    for workout in source:
                        source_date = date.fromisoformat(workout["date"])
                        target = source_date + timedelta(days=7)
                        if target.isoformat() in by_date:
                            continue
                        api.post("/workouts", {"date": target.isoformat(), "name": workout["name"], "is_rest_day": workout.get("is_rest_day", False)})
                        copied += 1
                    notify(f"Скопировано тренировок: {copied}" if copied else "На прошлой неделе нечего копировать")
                    draw()
                except ApiError as exc:
                    notify(str(exc), True)

            if not selected:
                planner.controls.append(AppCard(ft.Column([
                    ft.Text("План на " + selected_date.strftime("%d.%m"), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Запланируйте тренировку или день отдыха.", color=TEXT_SECONDARY),
                    ft.Row([
                        PrimaryButton("Push", on_click=lambda _: create_from_template("Push"), expand=True),
                        PrimaryButton("Pull", on_click=lambda _: create_from_template("Pull"), expand=True),
                        PrimaryButton("Legs", on_click=lambda _: create_from_template("Legs"), expand=True),
                    ], spacing=8),
                    SecondaryButton("День отдыха", icon=ft.Icons.HOTEL, on_click=lambda _: create_from_template("Отдых", True), expand=True),
                    SecondaryButton("Копировать прошлую неделю", icon=ft.Icons.CONTENT_COPY, on_click=copy_last_week, expand=True),
                ], spacing=10, tight=True)))
            else:
                planner.controls.append(ft.Row([section_title(selected["name"]), ft.IconButton(ft.Icons.CONTENT_COPY, tooltip="Копировать прошлую неделю", on_click=copy_last_week)]))
                planner.controls.append(active_session(selected, exercises))
            return [planner]

        async def _load():
            try:
                controls = await asyncio.to_thread(_fetch_and_build)
                root.controls.clear()
                root.controls.extend(controls)
            finally:
                hide_loading(page, overlay)
                page.update()

        page.run_task(_load)

    def select_date(value: date) -> None:
        nonlocal selected_date
        selected_date = value
        draw()

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
        rest_label.value = "Отдых: готов"
        selected_exercise = ft.Dropdown(label="Упражнение", options=[ft.dropdown.Option(key=item["id"], text=item["name"]) for item in exercises], expand=True)
        weight = AppTextField("Вес, кг", keyboard_type=ft.KeyboardType.NUMBER)
        weight.width = 105
        reps = AppTextField("Повторы", keyboard_type=ft.KeyboardType.NUMBER)
        reps.width = 95
        rir = AppTextField("RIR", keyboard_type=ft.KeyboardType.NUMBER, value="2")
        rir.width = 70
        rest = AppTextField("Отдых, сек", keyboard_type=ft.KeyboardType.NUMBER, value="90")
        rest.width = 110
        flag_state: dict[str, bool] = {"warmup": False, "failure": False, "dropset": False, "superset": False}

        def make_flag(key: str, label: str) -> ft.Control:
            return AppCheckbox(flag_state[key], lambda value, k=key: flag_state.__setitem__(k, value), label)

        flags_row = ft.Row([make_flag(key, label) for key, label in FLAG_DEFS], wrap=True, spacing=8)

        def refresh_flags() -> None:
            flags_row.controls.clear()
            flags_row.controls.extend(make_flag(key, label) for key, label in FLAG_DEFS)
            flags_row.update()

        last_hint = ft.Text("", size=12, color=TEXT_SECONDARY)
        expanded: dict[str, bool] = {}

        async def rest_timer(seconds: int) -> None:
            if seconds <= 0:
                return
            for remaining in range(seconds, -1, -1):
                try:
                    rest_label.value = f"Отдых: {remaining} сек"
                    ring.set_value((1 - remaining / seconds) * 100)
                except RuntimeError:
                    # Controls detached (navigated away / screen rebuilt) —
                    # set_value() calls update() which would raise; stop ticking.
                    break
                page.update()
                await asyncio.sleep(1)
            try:
                rest_label.value = "Отдых завершён"
                ring.set_value(0)
                page.update()
            except RuntimeError:
                pass

        def exercise_by_id(exercise_id: str) -> dict:
            return next((item for item in exercises if item["id"] == exercise_id), {"name": "Упражнение"})

        def pick_exercise(exercise_id: str) -> None:
            selected_exercise.value = exercise_id
            selected_exercise.update()
            last_hint.value = last_session_text(exercise_id, workout["id"]) or ""
            last_hint.update()
            weight.focus()

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
                payload = {"exercise_id": selected_exercise.value, "order": len(grouped), "set_number": len(existing) + 1, "weight_kg": float(weight.value), "reps": int(reps.value), "rir": int(rir.value) if rir.value else None, "rest_sec": int(rest.value) if rest.value else None, "is_warmup": bool(flag_state["warmup"]), "is_failure": bool(flag_state["failure"]), "is_dropset": bool(flag_state["dropset"]), "is_superset": bool(flag_state["superset"])}
                result = api.post(f"/workouts/{workout['id']}/sets", payload)
                notify("🏆 Новый рекорд!" if result["is_pr"] else f"Сет сохранён · 1RM: {result['one_rm']:.1f} кг")
                page.run_task(rest_timer, int(rest.value or 90))
                draw()
            except (TypeError, ValueError, ApiError) as exc:
                notify(str(exc), True)

        def copy_last_set(_: ft.ControlEvent, exercise_id: str) -> None:
            previous = last_session_text(exercise_id, workout["id"])
            source = [item for item in api.get(f"/exercises/{exercise_id}/history") if item["workout_id"] != workout["id"]]
            if not source:
                notify("Прошлых сетов нет", True)
                return
            template = source[0]
            selected_exercise.value = exercise_id
            weight.value = str(template["weight_kg"])
            reps.value = str(template["reps"])
            rir.value = str(template.get("rir") or 2)
            rest.value = str(template.get("rest_sec") or 90)
            flag_state["warmup"] = bool(template.get("is_warmup"))
            flag_state["failure"] = bool(template.get("is_failure"))
            for field in (selected_exercise, weight, reps, rir, rest):
                field.update()
            refresh_flags()
            notify(f"Скопирован прошлый сет · {previous or ''}")

        def drop_set(_: ft.ControlEvent, exercise_id: str) -> None:
            items = grouped.get(exercise_id)
            if not items:
                notify("Сначала добавьте сет", True)
                return
            template = items[-1]
            selected_exercise.value = exercise_id
            weight.value = str(round(template["weight_kg"] * 0.8, 1))
            reps.value = str(template["reps"])
            flag_state["dropset"] = True
            for field in (selected_exercise, weight, reps):
                field.update()
            refresh_flags()
            weight.focus()
            notify("Заполнен дроп-сет (−20% веса)")

        def toggle_superset(_: ft.ControlEvent, exercise_id: str) -> None:
            flag_state["superset"] = not flag_state["superset"]
            selected_exercise.value = exercise_id
            selected_exercise.update()
            refresh_flags()
            notify("Суперсет включён" if flag_state["superset"] else "Суперсет выключен")

        def toggle_expand(exercise_id: str) -> None:
            expanded[exercise_id] = not expanded.get(exercise_id, True)
            draw()

        exercise_blocks = []
        for exercise_id in grouped:
            items = grouped[exercise_id]
            name = exercise_by_id(exercise_id)["name"]
            tonnage = sum(item["weight_kg"] * item["reps"] for item in items if not item["is_warmup"])
            best = max(item["one_rm"] for item in items)
            previous = last_session_text(exercise_id, workout["id"]) or "Прошлый: нет данных"
            is_open = expanded.get(exercise_id, True)
            header = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(name, weight=ft.FontWeight.W_600, size=15),
                        ft.Text(f"{len(items)} сетов · тоннаж {tonnage:.0f} кг · лучший 1RM {best:.1f}", size=12, color=TEXT_SECONDARY),
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
                        ft.Text(f"1RM {item['one_rm']:.1f}", size=12, color=TEXT_SECONDARY),
                    ]), padding=12))
                group_controls.append(ft.Row([
                    ft.TextButton("+ сет", icon=ft.Icons.ADD, on_click=lambda _, value=exercise_id: pick_exercise(value)),
                    ft.TextButton("Копировать прошлый", icon=ft.Icons.CONTENT_COPY, on_click=lambda _, value=exercise_id: copy_last_set(_, value)),
                    ft.TextButton("Дроп-сет", icon=ft.Icons.TRENDING_DOWN, on_click=lambda _, value=exercise_id: drop_set(_, value)),
                    ft.TextButton("Суперсет", icon=ft.Icons.SWAP_HORIZ, on_click=lambda _, value=exercise_id: toggle_superset(_, value)),
                    ft.TextButton("Свернуть", icon=ft.Icons.KEYBOARD_ARROW_UP, on_click=lambda _, value=exercise_id: toggle_expand(value)),
                ], wrap=True, spacing=0))
            exercise_blocks.append(ft.Container(
                content=ft.Column(group_controls, spacing=8, tight=True),
                padding=12, border_radius=12, bgcolor=COLORS["bg_tertiary"],
            ))

        def finish(_: ft.ControlEvent) -> None:
            duration = AppTextField("Длительность, мин", keyboard_type=ft.KeyboardType.NUMBER)
            difficulty = ft.Slider(min=1, max=10, divisions=9, value=7, label="Сложность: {value}")
            pump = ft.Slider(min=1, max=10, divisions=9, value=7, label="Памп: {value}")
            energy = ft.Slider(min=1, max=10, divisions=9, value=7, label="Энергия: {value}")
            pain_state = {"value": False}
            pain = AppCheckbox(False, lambda value: pain_state.__setitem__("value", value), "Была боль")
            comment = AppTextField("Комментарий")

            def save(_: ft.ControlEvent) -> None:
                try:
                    api.put(f"/workouts/{workout['id']}", {"completed": True, "duration_min": int(duration.value or 0), "difficulty": int(difficulty.value), "pump": int(pump.value), "energy_level": int(energy.value), "pain": bool(pain_state["value"]), "comment": comment.value or None})
                    page.pop_dialog()
                    draw()
                    notify("Тренировка завершена")
                except ApiError as exc:
                    notify(str(exc), True)

            sheet_content = ft.Column([
                ft.Text("Завершить тренировку", size=20, weight=ft.FontWeight.BOLD),
                duration, difficulty, pump, energy, pain, comment,
                ft.Row([
                    SecondaryButton("Отмена", on_click=lambda _: page.pop_dialog()),
                    PrimaryButton("Сохранить", icon=ft.Icons.CHECK, on_click=save, expand=True),
                ], spacing=12),
            ], tight=True, spacing=10)
            show_bottom_sheet(page, sheet_content)

        return AppCard(ft.Column([
            section_title(workout["name"], Chip("Готово", SUCCESS, SUCCESS + "33") if workout["completed"] else Chip("Сессия", ACCENT, ACCENT + "22")),
            ft.Text(f"Тоннаж: {workout['total_tonnage']:.0f} кг", color=ACCENT),
            *(exercise_blocks or [ft.Container(content=ft.Text("Добавьте первое упражнение", color=TEXT_SECONDARY), padding=6)]),
            ft.Divider(),
            ft.Text("Добавить сет", size=16, weight=ft.FontWeight.W_600),
            # ВАЖНО (flet 0.86): нельзя expand-ребёнка (Dropdown) внутри Row(wrap=True) —
            # клиент заливает весь экран серым (#b7b7b7). Dropdown — отдельной строкой.
            ft.Row([selected_exercise]),
            ft.Row([weight, reps], wrap=True),
            last_hint,
            ft.Row([rir, rest], wrap=True),
            flags_row,
            ft.Row([PrimaryButton("+ Сет", icon=ft.Icons.ADD, on_click=add_set), ring, rest_label], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            PrimaryButton("Завершить тренировку", icon=ft.Icons.CHECK, on_click=finish),
        ], spacing=10, tight=True))

    draw()
    return root
