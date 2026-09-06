import asyncio
from datetime import date, timedelta

import flet as ft

from api_client import ApiClient, ApiError
from components.buttons import SecondaryButton
from components.card import AppCard, section_title
from components.charts import line_chart, pie_chart
from components.chips import Chip
from components.loading import hide_loading, show_loading
from components.scaffold import MetricCard
from components.sheets import show_bottom_sheet
from theme import ACCENT, COLORS, ERROR, SUCCESS, TEXT_SECONDARY, WARNING

TABS = ["Календарь", "Вес", "Питание", "Протокол", "Анализы"]
PERIODS = [(7, "7 дней"), (30, "30 дней"), (90, "90 дней")]


def analytics_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    active = 0
    calendar_month = date.today().replace(day=1)
    nutrition_period = 30
    root = ft.Column(expand=True)

    def notify(text: str, error: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if error else SUCCESS))

    def summary_row(*metrics: ft.Control | None) -> ft.Row:
        """Horizontal (scrollable) strip of MetricCards for key figures."""
        metrics = [metric for metric in metrics if metric is not None]
        return ft.Row(metrics, scroll=ft.ScrollMode.AUTO, spacing=12)

    def draw() -> None:
        # Show the loader immediately, run the blocking httpx fetch + control
        # build in a worker thread, then attach the result on the main loop.
        overlay = show_loading(page, "Загрузка данных...")

        def _fetch_and_build():
            tab_bar = ft.Row([], scroll=ft.ScrollMode.AUTO, spacing=8)
            for index, name in enumerate(TABS):
                selected = index == active
                tab_bar.controls.append(ft.Container(
                    content=Chip(
                        name,
                        color=ACCENT if selected else TEXT_SECONDARY,
                        bg=(ACCENT + "26") if selected else COLORS["bg_tertiary"],
                    ),
                    padding=ft.Padding.symmetric(horizontal=2, vertical=6),
                    on_click=lambda _, value=index: choose(value),
                    ink=True,
                ))
            content = ft.ListView(expand=True, spacing=12, padding=16)
            try:
                if active == 0:
                    calendar_view(content)
                elif active == 1:
                    weight_view(content)
                elif active == 2:
                    nutrition_view(content)
                elif active == 3:
                    protocol_view(content)
                else:
                    lab_view(content)
            except ApiError as exc:
                content.controls.append(ft.Text(str(exc), color=ERROR))
            return [ft.Container(content=tab_bar, padding=ft.Padding.only(left=16, right=16, top=12)), content]

        async def _load():
            try:
                controls = await asyncio.to_thread(_fetch_and_build)
                root.controls.clear()
                root.controls.extend(controls)
            finally:
                hide_loading(page, overlay)
                page.update()

        page.run_task(_load)

    def choose(index: int) -> None:
        nonlocal active
        active = index
        draw()

    def calendar_view(content: ft.ListView) -> None:
        month = calendar_month.strftime("%Y-%m")
        days = {item["date"]: item for item in api.get("/analytics/calendar", {"month": month})}
        first = calendar_month
        next_month = date(first.year + (first.month == 12), 1 if first.month == 12 else first.month + 1, 1)
        month_len = (next_month - first).days
        cells = [ft.Container(width=43, height=43) for _ in range(first.weekday())]
        for day_number in range(1, month_len + 1):
            current = date(first.year, first.month, day_number).isoformat()
            item = days.get(current)
            color = item["color"] if item else "#374151"
            cells.append(ft.Container(content=ft.Text(str(day_number), text_align=ft.TextAlign.CENTER), alignment=ft.Alignment.CENTER, width=43, height=43, bgcolor=color + "66", border=ft.Border.all(1, color), border_radius=10, on_click=lambda _, value=current: day_summary(value), ink=True))

        def shift(step: int) -> None:
            nonlocal calendar_month
            index = calendar_month.year * 12 + (calendar_month.month - 1) + step
            calendar_month = date(index // 12, index % 12 + 1, 1)
            draw()

        content.controls.extend([
            section_title("Календарь", ft.Row([ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda _: shift(-1)), ft.Text(first.strftime("%B %Y"), color=TEXT_SECONDARY), ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda _: shift(1))], tight=True)),
            ft.Row([ft.Text(name, width=43, text_align=ft.TextAlign.CENTER, color=TEXT_SECONDARY, size=11) for name in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]]),
            ft.Row(cells, wrap=True, spacing=5, run_spacing=5),
            AppCard(ft.Row([
                ft.Text("🟢 закрыт 100%", size=12, color=TEXT_SECONDARY),
                ft.Text("🟡 частично", size=12, color=TEXT_SECONDARY),
                ft.Text("🔴 пропуски", size=12, color=TEXT_SECONDARY),
                ft.Text("🟣 анализы", size=12, color=TEXT_SECONDARY),
                ft.Text("⚪ пусто", size=12, color=TEXT_SECONDARY),
            ], wrap=True, spacing=8)),
        ])

    def day_summary(day_value: str) -> None:
        try:
            item = api.get(f"/days/{day_value}")
        except ApiError as exc:
            notify(str(exc), True)
            return
        day = item["day"]
        uncompleted = item["uncompleted"]
        missing = list(uncompleted.get("protocol") or [])
        if uncompleted.get("workout"):
            missing.append("Тренировка")
        if uncompleted.get("nutrition"):
            missing.append("Питание")
        if uncompleted.get("metrics"):
            missing.append("Метрики")
        rows = [
            ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ACCENT), ft.Text(f"Выполнение: {day['completion_pct']}%", expand=True)], spacing=8),
            ft.Row([ft.Icon(ft.Icons.RESTAURANT, size=16, color=TEXT_SECONDARY), ft.Text(f"Приёмов пищи: {item['meal_count']}", expand=True)], spacing=8),
            ft.Row([ft.Icon(ft.Icons.FITNESS_CENTER, size=16, color=TEXT_SECONDARY), ft.Text(f"Тренировок: {len(item['workouts'])}", expand=True)], spacing=8),
            ft.Row([ft.Icon(ft.Icons.MEDICATION, size=16, color=TEXT_SECONDARY), ft.Text("Протокол: " + (", ".join(uncompleted.get("protocol") or []) or "выполнен"), expand=True)], spacing=8),
        ]
        if missing:
            rows.append(ft.Text("Незавершено: " + ", ".join(missing), size=12, color=WARNING))
        sheet_content = ft.Column([
            ft.Text(day_value, size=20, weight=ft.FontWeight.BOLD),
            AppCard(ft.Column(rows, spacing=10, tight=True), padding=12),
            SecondaryButton("Закрыть", icon=ft.Icons.CLOSE, on_click=lambda _: page.pop_dialog(), expand=True),
        ], tight=True, spacing=10)
        show_bottom_sheet(page, sheet_content)

    def weight_view(content: ft.ListView) -> None:
        end = date.today()
        start = end - timedelta(days=90)
        data = api.get("/analytics/weight", {"from": start.isoformat(), "to": end.isoformat()})
        points = data["points"]
        content.controls.append(section_title("Вес", ft.Text(f"Δ {data['delta']:+.1f} кг", color=ACCENT)))
        if points:
            last = points[-1]["weight_kg"]
            content.controls.append(summary_row(MetricCard("Вес сегодня", f"{last:.1f}", "кг", icon=ft.Icons.MONITOR_WEIGHT, color=ACCENT)))
            content.controls.append(AppCard(line_chart({"Вес": [item["weight_kg"] for item in points], "MA7": [item["value"] for item in data["ma7"]], "MA30": [item["value"] for item in data["ma30"]]}, [str(item["date"])[5:] for item in points])))
        else:
            content.controls.append(AppCard(ft.Text("Добавьте измерения веса на экране «Сегодня».", color=TEXT_SECONDARY)))

    def nutrition_view(content: ft.ListView) -> None:
        def period_buttons() -> ft.Control:
            return ft.Row([
                # ВАЖНО (flet 0.86): selected — list, не set (msgpack).
                ft.SegmentedButton(
                    selected=[str(nutrition_period)],
                    segments=[ft.Segment(value=str(days), label=ft.Text(text)) for days, text in PERIODS],
                    on_change=choose_nutrition_period,
                    show_selected_icon=False,
                ),
            ])

        end = date.today()
        data = api.get("/analytics/nutrition", {"from": (end - timedelta(days=nutrition_period - 1)).isoformat(), "to": end.isoformat()})
        averages = data["averages"]
        macros = [
            ft.Row([ft.Text("Белки", size=13, expand=True), ft.Text(f"{averages['protein_g']:.0f} г", color=TEXT_SECONDARY)]),
            ft.Row([ft.Text("Жиры", size=13, expand=True), ft.Text(f"{averages['fat_g']:.0f} г", color=TEXT_SECONDARY)]),
            ft.Row([ft.Text("Углеводы", size=13, expand=True), ft.Text(f"{averages['carbs_g']:.0f} г", color=TEXT_SECONDARY)]),
        ]
        content.controls.extend([
            section_title("Питание", period_buttons()),
            summary_row(MetricCard("Ккал в среднем", f"{averages['kcal']:.0f}", "ккал", icon=ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ACCENT)),
            AppCard(ft.Column([
                ft.Text("Макроэлементы в среднем", weight=ft.FontWeight.W_600),
                *macros,
            ], spacing=8, tight=True)),
            AppCard(ft.Column([
                ft.Text("Распределение макроэлементов", weight=ft.FontWeight.W_600),
                pie_chart({"Белки": averages["protein_g"] * 4, "Жиры": averages["fat_g"] * 9, "Углеводы": averages["carbs_g"] * 4}),
            ], spacing=10, tight=True)),
            ft.Text("Дни выше лимита калорий: " + (", ".join(str(value)[5:] for value in data["over_calorie_days"]) or "нет"), color=TEXT_SECONDARY),
        ])

    def choose_nutrition_period(event: ft.ControlEvent) -> None:
        nonlocal nutrition_period
        nutrition_period = int(event.control.selected[0])
        draw()

    def protocol_view(content: ft.ListView) -> None:
        end = date.today()
        data = api.get("/analytics/protocol", {"from": (end - timedelta(days=6)).isoformat(), "to": end.isoformat()})
        content.controls.append(section_title("Протокол"))
        content.controls.append(summary_row(MetricCard("Выполнение за неделю", f"{data['completion_pct']:.0f}", "%", icon=ft.Icons.CHECK_CIRCLE, color=ACCENT)))
        content.controls.append(AppCard(ft.Column([
            ft.Text("Недельный прогресс", weight=ft.FontWeight.W_600),
            ft.ProgressBar(value=data["completion_pct"] / 100, color=ACCENT),
        ], spacing=10, tight=True)))
        content.controls.append(AppCard(ft.Column([
            ft.Text("Чаще всего пропущены", weight=ft.FontWeight.W_600),
            *([ft.Text(f"{row['item']}: {row['missed']}") for row in data["top_missed"]] or [ft.Text("Нет пропусков", color=TEXT_SECONDARY)]),
        ], spacing=8, tight=True)))
        content.controls.append(AppCard(ft.Column([
            ft.Text("Остатки", weight=ft.FontWeight.W_600),
            *([ft.Text(f"⚠ {row['name']}: {row['stock_remaining']}") for row in data["stock_warnings"]] or [ft.Text("Предупреждений нет", color=TEXT_SECONDARY)]),
        ], spacing=8, tight=True)))

    def lab_view(content: ft.ListView) -> None:
        tests = api.get("/lab/tests")
        content.controls.append(section_title("Анализы", ft.TextButton("Добавить", on_click=lambda _: add_lab())))
        for test in tests:
            markers = test["markers"]
            rows = []
            for marker in markers:
                trend = marker_trend(marker["name"])
                icon = ft.Icons.ARROW_UPWARD if trend == "up" else ft.Icons.ARROW_DOWNWARD if trend == "down" else ft.Icons.REMOVE
                color = ERROR if marker["flag"] in {"high", "low"} else SUCCESS
                rows.append(ft.Row([
                    ft.Text(marker["name"], expand=True),
                    ft.Text(f"{marker['value']} {marker['unit']}"),
                    ft.Icon(icon, color=color, tooltip="Динамика к прошлому анализу" if trend != "flat" else "Без изменений"),
                ]))
            rows.append(ft.TextButton("Добавить маркер", icon=ft.Icons.ADD, on_click=lambda _, value=test: add_marker(value)))
            content.controls.append(AppCard(ft.Column([
                ft.Text(f"{test['date']} · {test.get('panel_name') or 'Панель'}", weight=ft.FontWeight.W_600),
                *rows,
            ], spacing=8, tight=True)))

    def marker_trend(name: str) -> str:
        try:
            history = api.get("/lab/markers/history", {"name": name})
        except ApiError:
            return "flat"
        if len(history) < 2:
            return "flat"
        latest, previous = history[-1]["value"], history[-2]["value"]
        if latest > previous:
            return "up"
        if latest < previous:
            return "down"
        return "flat"

    def add_lab() -> None:
        panel = ft.TextField(label="Название панели")
        laboratory = ft.TextField(label="Лаборатория")

        def save(_: ft.ControlEvent) -> None:
            try:
                api.post("/lab/tests", {"date": date.today().isoformat(), "panel_name": panel.value or None, "lab": laboratory.value or None})
                page.pop_dialog()
                draw()
            except ApiError as exc:
                notify(str(exc), True)

        dialog = ft.AlertDialog(title=ft.Text("Новый анализ"), content=ft.Column([panel, laboratory], tight=True), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Создать", on_click=save)])
        page.show_dialog(dialog)

    def add_marker(test: dict) -> None:
        name = ft.TextField(label="Маркер")
        value = ft.TextField(label="Значение", keyboard_type=ft.KeyboardType.NUMBER)
        unit = ft.TextField(label="Единица")
        category = ft.TextField(label="Категория", hint_text="ОАК / биохимия / гормоны / ...")
        ref_min = ft.TextField(label="Реф. минимум", keyboard_type=ft.KeyboardType.NUMBER)
        ref_max = ft.TextField(label="Реф. максимум", keyboard_type=ft.KeyboardType.NUMBER)

        def save(_: ft.ControlEvent) -> None:
            try:
                api.post(f"/lab/tests/{test['id']}/markers", {"category": category.value or "прочее", "name": name.value, "value": float(value.value), "unit": unit.value, "ref_min": float(ref_min.value) if ref_min.value else None, "ref_max": float(ref_max.value) if ref_max.value else None})
                page.pop_dialog()
                notify("Маркер добавлен")
                draw()
            except (TypeError, ValueError, ApiError) as exc:
                notify(str(exc), True)

        dialog = ft.AlertDialog(title=ft.Text(f"Маркер · {test.get('panel_name') or test['date']}"), content=ft.Column([name, value, unit, category, ref_min, ref_max], tight=True, scroll=ft.ScrollMode.AUTO), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Сохранить", on_click=save)])
        page.show_dialog(dialog)

    draw()
    return root
