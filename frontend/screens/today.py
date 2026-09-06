from datetime import date, timedelta

import flet as ft

from api_client import ApiClient, ApiError
from components.buttons import PrimaryButton
from components.card import card, section_title
from components.chips import Chip
from components.circular_progress import CircularProgress
from components.inputs import AppCheckbox
from components.progress import ProgressBar
from theme import ACCENT, COLORS, ERROR, SUCCESS, TEXT, TEXT_SECONDARY, TEXT_TERTIARY, WARNING

WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
BASE_GOALS = {"kcal": 2600, "protein_g": 180, "fat_g": 80, "carbs_g": 300, "fiber_g": 30, "water_ml": 2500}


def goals_for(day_type: str) -> dict[str, float]:
    goals = dict(BASE_GOALS)
    if day_type == "rest":
        goals["kcal"] *= 0.85
    elif day_type == "refeed":
        goals["kcal"] *= 1.1
        goals["carbs_g"] *= 1.25
    return goals


def today_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    root = ft.ListView(expand=True, spacing=12, padding=16)

    def message(text: str, error: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if error else SUCCESS))

    try:
        data = api.get("/days/today")
    except ApiError as exc:
        return ft.Container(content=ft.Text(str(exc)), padding=24)

    day = data["day"]
    today = date.fromisoformat(day["date"])
    day_type = day.get("day_type") or "training"
    goals = goals_for(day_type)

    progress = CircularProgress(day["completion_pct"], size=80, stroke=8, gradient=True)
    closed_chip = Chip("День закрыт", SUCCESS, SUCCESS + "33") if day.get("closed") else None
    header = card(
        ft.Row([
            ft.Column([
                ft.Text("Сегодня", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"{WEEKDAYS[today.weekday()]} · {day_type}", color=TEXT_SECONDARY),
            ], expand=True),
            ft.Column([
                ft.Text(today.strftime("%d.%m.%Y").upper(), size=11, color=TEXT_TERTIARY, text_align=ft.TextAlign.RIGHT),
                progress,
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=8, tight=True),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        *([closed_chip] if closed_chip else []),
    )
    root.controls.append(header)

    metric = data.get("metric") or {}

    # Weight delta versus the previous recorded measurement.
    try:
        history = api.get("/body-metrics", {"from": (today - timedelta(days=30)).isoformat(), "to": today.isoformat()})
        weights = [item for item in history if item.get("weight_kg")]
        weight_delta = round(weights[-1]["weight_kg"] - weights[-2]["weight_kg"], 1) if len(weights) > 1 else None
    except ApiError:
        weight_delta = None

    metric_defs = [("Вес", "weight_kg", "кг"), ("Сон", "sleep_hours", "ч"), ("Энергия", "energy", "/10"), ("Аппетит", "appetite", "/10"), ("Настроение", "mood", "/10"), ("Самочувствие", "wellbeing", "/10")]

    def show_metric_sheet(label: str, key: str, unit: str) -> None:
        initial = metric.get(key)
        if initial is None:
            initial = 70 if key == "weight_kg" else 7
        numeric = ft.TextField(value=str(initial), label=f"{label}, {unit}", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        scale = key in {"energy", "appetite", "mood", "wellbeing", "sleep_quality"}
        slider = ft.Slider(min=1, max=10, divisions=9, value=float(initial), label="{value}", on_change=lambda _: sync_from_slider()) if scale else None

        def sync_from_slider() -> None:
            if slider:
                numeric.value = str(round(slider.value))
                numeric.update()

        def sync_from_field(_: ft.ControlEvent) -> None:
            if slider:
                try:
                    slider.value = float(numeric.value or 1)
                    slider.update()
                except ValueError:
                    pass

        numeric.on_change = sync_from_field

        def save(_: ft.ControlEvent) -> None:
            try:
                payload = {"date": day["date"], "weight_kg": float(metric.get("weight_kg") or 70), key: float(numeric.value or 0)}
                if scale:
                    payload[key] = int(max(1, min(10, float(numeric.value or 1))))
                api.post("/body-metrics", payload)
                page.pop_dialog()
                message("Метрика сохранена")
                navigate(0)
            except (TypeError, ValueError, ApiError) as exc:
                message(str(exc), True)

        sheet = ft.BottomSheet(ft.Container(content=ft.Column([ft.Text(f"Отметить: {label}", size=20, weight=ft.FontWeight.BOLD), numeric, *([slider] if slider else []), ft.FilledButton("Сохранить", on_click=save, height=48)], tight=True), padding=20))
        page.show_dialog(sheet)

    metric_tiles = []
    for label, key, unit in metric_defs:
        value = metric.get(key)
        shown = "—" if value is None else f"{value}{unit}"
        extras = []
        if key == "weight_kg" and weight_delta is not None:
            color = SUCCESS if weight_delta <= 0 else WARNING
            extras.append(ft.Text(f"{weight_delta:+.1f} кг", size=11, color=color))
        metric_tiles.append(ft.Container(content=ft.Column([ft.Text(label, color=TEXT_SECONDARY, size=12), ft.Text(shown, size=17, weight=ft.FontWeight.W_600), *extras], tight=True), padding=12, width=120, height=100, border_radius=12, bgcolor=COLORS["bg_tertiary"], on_click=lambda e, a=label, b=key, c=unit: show_metric_sheet(a, b, c), ink=True))
    root.controls.append(ft.Column([section_title("Метрики"), ft.Row(metric_tiles, scroll=ft.ScrollMode.AUTO)]))

    nutrition = data["nutrition"]
    labels = [("Ккал", "kcal"), ("Белки", "protein_g"), ("Жиры", "fat_g"), ("Углеводы", "carbs_g"), ("Клетчатка", "fiber_g"), ("Вода", "water_ml")]
    bars = []
    for label, key in labels:
        current = nutrition.get(key) or 0
        goal = goals[key]
        unit = "мл" if key == "water_ml" else "г" if key != "kcal" else ""
        bars.append(ft.Column([
            ft.Row([ft.Text(label, size=12), ft.Text(f"{current:.0f}/{goal:.0f} {unit}".strip(), size=12, color=WARNING if current > goal else TEXT_SECONDARY, expand=True, text_align=ft.TextAlign.RIGHT)]),
            ProgressBar(current, goal, over_color=(WARNING if current > goal else ACCENT)),
        ], spacing=3))
    root.controls.append(card(section_title("Питание", ft.TextButton("Открыть", on_click=lambda _: navigate(2))), *bars, on_click=lambda _: navigate(2)))

    protocol_rows = []
    for item in data["protocol"]:
        def quick_log(_: ft.ControlEvent, protocol_item=item) -> None:
            try:
                api.post(f"/protocol/items/{protocol_item['id']}/log", {})
                message("Приём отмечен")
                navigate(0)
            except ApiError as exc:
                message(str(exc), True)
        time_text = ", ".join(value[:5] for value in item.get("schedule_times") or []) or "в течение дня"
        protocol_rows.append(ft.Row([
            ft.Column([ft.Text(item["name"], weight=ft.FontWeight.W_500), ft.Text(f"{time_text} · {item['planned_dose_value']} {item['planned_dose_unit']}", size=12, color=TEXT_SECONDARY)], expand=True),
            Chip("Принято" if item["taken"] else "Ожидается", SUCCESS if item["taken"] else WARNING, (SUCCESS + "33") if item["taken"] else (WARNING + "22")),
            ft.IconButton(ft.Icons.DONE, icon_color=ACCENT, tooltip="Отметить", on_click=quick_log),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
    root.controls.append(card(section_title("Протокол", ft.TextButton("Все", on_click=lambda _: navigate(3))), *(protocol_rows or [ft.Text("Нет обязательных приёмов", color=TEXT_SECONDARY)])))

    # Daily checks: local UI state with all required input types.
    check_state = {"activity": False}
    check_active = AppCheckbox(False, lambda value: check_state.update(activity=value), "Активность выполнена")
    steps = ft.TextField(label="Шаги", keyboard_type=ft.KeyboardType.NUMBER, value="")
    wake = ft.TextField(label="Подъём (HH:MM)", value="")
    comment = ft.TextField(label="Комментарий к дню", multiline=True, min_lines=1, max_lines=2)
    stress = ft.Slider(min=1, max=10, divisions=9, value=5, label="Стресс: {value}")
    root.controls.append(card(section_title("Ежедневные проверки"), check_active, steps, wake, comment, stress))

    def close_day(_: ft.ControlEvent) -> None:
        if day.get("closed"):
            message("День уже закрыт", True)
            return
        uncompleted = data["uncompleted"]
        labels = list(uncompleted.get("protocol") or [])
        if uncompleted.get("workout"):
            labels.append("Тренировка")
        if uncompleted.get("nutrition"):
            labels.append("Питание")
        if uncompleted.get("metrics"):
            labels.append("Метрики")
        reason = ft.TextField(label="Причина (необязательно)", multiline=True)

        def confirm(_: ft.ControlEvent) -> None:
            try:
                api.post(f"/days/{day['date']}/close", {"reason": reason.value or None})
                page.pop_dialog()
                message("День закрыт")
                navigate(0)
            except ApiError as exc:
                message(str(exc), True)

        dialog = ft.AlertDialog(
            title=ft.Text("Закрыть день?"),
            content=ft.Column([
                ft.Text(f"Выполнение: {day['completion_pct']}%", weight=ft.FontWeight.W_600),
                ft.Text("Незавершено: " + (", ".join(labels) if labels else "всё выполнено"), color=TEXT_SECONDARY),
                reason,
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Закрыть", on_click=confirm)],
        )
        page.show_dialog(dialog)

    root.controls.append(PrimaryButton("Закрыть день" if not day.get("closed") else "День закрыт ✓", icon=ft.Icons.LOCK, on_click=close_day, disabled=bool(day.get("closed"))))
    return root
