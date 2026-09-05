from datetime import date

import flet as ft

from api_client import ApiClient, ApiError
from components.body_map import BodyMap
from components.card import card, section_title
from components.chips import Chip
from theme import ACCENT, ERROR, SUCCESS, TEXT_SECONDARY, TEXT_TERTIARY, WARNING


def protocol_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    root = ft.Column(expand=True)

    def notify(text: str, bad: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if bad else SUCCESS))

    def draw() -> None:
        root.controls.clear()
        try:
            items = api.get("/protocol/items")
            schedule = {item["id"]: api.get(f"/protocol/items/{item['id']}/schedule", {"date": date.today().isoformat()}) for item in items}
            rotation = api.get("/protocol/rotation")
        except ApiError as exc:
            root.controls.append(ft.Text(str(exc))); page.update(); return
        view = ft.ListView(expand=True, spacing=12, padding=16)
        view.controls.append(section_title("Протокол", ft.IconButton(ft.Icons.ADD, icon_color=ACCENT, tooltip="Создать", on_click=lambda _: edit_item())))
        grouped = {"Утро": [], "С едой": [], "Вечер": [], "На ночь": []}
        for item in items:
            times = item.get("schedule_times") or []
            hour = int(times[0].split(":")[0]) if times else 12
            title = "Утро" if hour < 11 else "С едой" if hour < 17 else "Вечер" if hour < 21 else "На ночь"
            grouped[title].append(item)
        for title, group in grouped.items():
            if not group: continue
            rows = []
            for item in group:
                logs = schedule[item["id"]]["logs"]
                taken = any(log["status"] == "taken" for log in logs)
                time_text = ", ".join(value[:5] for value in item.get("schedule_times") or []) or "по расписанию"
                rows.append(ft.Container(content=ft.Row([
                    ft.Column([ft.Text(item["name"], weight=ft.FontWeight.W_600), ft.Text(f"{time_text} · {item['planned_dose_value']} {item['planned_dose_unit']} · {item.get('route') or '—'}", size=12, color=TEXT_SECONDARY)], expand=True),
                    Chip("Принято" if taken else "Ожидается", SUCCESS if taken else WARNING, (SUCCESS + "33") if taken else (WARNING + "22")),
                    ft.IconButton(ft.Icons.DONE, icon_color=ACCENT, on_click=lambda _, entry=item: log_form(entry)),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e, entry=item: detail(entry), ink=True))
            view.controls.append(ft.Text(title.upper(), size=11, weight=ft.FontWeight.W_600, color=TEXT_TERTIARY))
            view.controls.append(card(*rows))

        def select_zone(zone: str) -> None:
            try:
                logs = api.get(f"/protocol/sites/{zone}/history")
                dialog = ft.AlertDialog(title=ft.Text(zone), content=ft.Column([ft.Text(f"{log['date']} {log['time'][:5]} · {log['actual_dose_value']} {log['actual_dose_unit']}") for log in logs] or [ft.Text("Нет записей")], tight=True), actions=[ft.TextButton("Закрыть", on_click=lambda _: page.pop_dialog())])
                page.show_dialog(dialog)
            except ApiError as exc: notify(str(exc), True)
        view.controls.append(card(
            section_title("Инъекции", ft.FilledButton("Авто-ротация", icon=ft.Icons.AUTORENEW, on_click=lambda _: notify("Предложенная зона: " + rotation["suggestion"]))),
            BodyMap(rotation["zones"], select_zone),
            ft.Text("Зелёный — использована недавно (< 7 дней); жёлтый — давно; серый — ещё не было. Нажмите на зону для истории.", size=12, color=TEXT_SECONDARY),
        ))
        root.controls.append(view); page.update()

    def log_form(item: dict) -> None:
        actual = ft.TextField(label="Фактическая доза", value=str(item["planned_dose_value"]), keyboard_type=ft.KeyboardType.NUMBER)
        unit = ft.Dropdown(label="Единица", value=item["planned_dose_unit"], options=[ft.dropdown.Option(item["planned_dose_unit"]), ft.dropdown.Option("mg"), ft.dropdown.Option("ml"), ft.dropdown.Option("mcg"), ft.dropdown.Option("IU"), ft.dropdown.Option("capsule")])
        moment = ft.TextField(label="Время (HH:MM)", value=date.today().strftime("%H:%M"))
        site = ft.Dropdown(label="Зона", value=item.get("default_site"), options=[ft.dropdown.Option(name) for name in ["дельта Л", "дельта П", "бицепс Л", "бицепс П", "квад Л", "квад П", "ягодица Л", "ягодица П", "живот", "бедро Л", "бедро П", "живот низ"]], visible=item["category"] == "injection")
        side = ft.Dropdown(label="Сторона", options=[ft.dropdown.Option("left", "Левая"), ft.dropdown.Option("right", "Правая")], visible=item["category"] == "injection")
        reaction = ft.TextField(label="Реакция", visible=item["category"] == "injection")
        comment = ft.TextField(label="Комментарий", multiline=True)
        def submit(force: bool = False) -> None:
            try:
                api.post(f"/protocol/items/{item['id']}/log", {"actual_dose_value": float(actual.value), "actual_dose_unit": unit.value, "time": moment.value + (":00" if len(moment.value) == 5 else ""), "site": site.value, "side": side.value, "reaction": reaction.value or None, "comment": comment.value or None, "force_duplicate": force})
                page.pop_dialog(); notify("Приём сохранён"); draw()
            except (TypeError, ValueError, ApiError) as exc:
                if "Уже отмечено" in str(exc) and not force:
                    duplicate = ft.AlertDialog(title=ft.Text("Повторный приём"), content=ft.Text(f"{exc}. Повторить?"), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Повторить", on_click=lambda _: (page.pop_dialog(), submit(True)))])
                    page.show_dialog(duplicate)
                else: notify(str(exc), True)
        dialog = ft.AlertDialog(title=ft.Text(item["name"]), content=ft.Column([actual, unit, moment, site, side, reaction, comment], tight=True, scroll=ft.ScrollMode.AUTO), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Подтвердить", on_click=lambda _: submit())])
        page.show_dialog(dialog)

    def detail(item: dict) -> None:
        try: history = api.get(f"/protocol/items/{item['id']}/history")
        except ApiError: history = []
        stock = item.get("stock_remaining")
        progress = min((stock or 0) / 30, 1) if stock is not None else 0
        dialog = ft.AlertDialog(title=ft.Text(item["name"]), content=ft.Column([ft.Text(f"План: {item['planned_dose_value']} {item['planned_dose_unit']}"), ft.Text(f"Остаток: {stock if stock is not None else 'не ведётся'}"), ft.ProgressBar(value=progress, color=WARNING if stock is not None and stock <= 7 else ACCENT), ft.Text("История", weight=ft.FontWeight.W_600), *[ft.Text(f"{entry['date']} {entry['time'][:5]} · {entry['actual_dose_value']} {entry['actual_dose_unit']}", size=12) for entry in history[:8]]], tight=True, scroll=ft.ScrollMode.AUTO), actions=[ft.TextButton("Редактировать", on_click=lambda _: (page.pop_dialog(), edit_item(item))), ft.TextButton("Закрыть", on_click=lambda _: page.pop_dialog())])
        page.show_dialog(dialog)

    def edit_item(existing: dict | None = None) -> None:
        item = existing or {}
        name = ft.TextField(label="Название", value=item.get("name", ""))
        category = ft.Dropdown(label="Категория", value=item.get("category", "supplement"), options=[ft.dropdown.Option(value) for value in ["supplement", "drug", "topical", "injection"]])
        dose = ft.TextField(label="Доза", value=str(item.get("planned_dose_value", "")), keyboard_type=ft.KeyboardType.NUMBER)
        unit = ft.Dropdown(label="Единица", value=item.get("planned_dose_unit", "mg"), options=[ft.dropdown.Option(value) for value in ["mg", "ml", "mcg", "IU", "capsule", "portion"]])
        times = ft.TextField(label="Время через запятую", value=", ".join(item.get("schedule_times") or []), hint_text="08:00, 20:00")
        weekdays = ft.TextField(label="Дни недели 1–7", value=", ".join(str(x) for x in item.get("weekdays") or []), hint_text="пусто = ежедневно")
        route = ft.Dropdown(label="Путь", value=item.get("route"), options=[ft.dropdown.Option(value) for value in ["oral", "im", "sc", "topical"]])
        start_date = ft.TextField(label="Начало (ГГГГ-ММ-ДД)", value=item.get("start_date") or date.today().isoformat())
        end_date = ft.TextField(label="Конец (пусто = бессрочно)", value=item.get("end_date") or "")
        default_site = ft.Dropdown(label="Зона по умолчанию", value=item.get("default_site"), options=[ft.dropdown.Option(zone) for zone in ["дельта Л", "дельта П", "бицепс Л", "бицепс П", "квад Л", "квад П", "ягодица Л", "ягодица П", "живот", "бедро Л", "бедро П", "живот низ"]], visible=item.get("category") == "injection")
        stock = ft.TextField(label="Остаток", value=str(item.get("stock_remaining") or ""), keyboard_type=ft.KeyboardType.NUMBER)
        required = ft.Checkbox(label="Обязательный", value=item.get("is_required", True))

        def on_category(_: ft.ControlEvent) -> None:
            default_site.visible = category.value == "injection"
            default_site.update()

        category.on_change = on_category

        def save(_: ft.ControlEvent) -> None:
            try:
                payload = {"name": name.value, "category": category.value, "planned_dose_value": float(dose.value), "planned_dose_unit": unit.value, "schedule_times": [part.strip() + (":00" if len(part.strip()) == 5 else "") for part in times.value.split(",") if part.strip()], "weekdays": [int(part) for part in weekdays.value.split(",") if part.strip()], "route": route.value, "default_site": default_site.value if category.value == "injection" else None, "start_date": date.fromisoformat(start_date.value).isoformat(), "end_date": date.fromisoformat(end_date.value).isoformat() if end_date.value else None, "stock_remaining": float(stock.value) if stock.value else None, "is_required": bool(required.value)}
                if existing:
                    api.put(f"/protocol/items/{existing['id']}", payload)
                else:
                    api.post("/protocol/items", payload)
                page.pop_dialog()
                draw()
            except (TypeError, ValueError, ApiError) as exc:
                notify(str(exc), True)

        dialog = ft.AlertDialog(title=ft.Text("Препарат"), content=ft.Column([name, category, dose, unit, times, weekdays, route, start_date, end_date, default_site, stock, required], tight=True, scroll=ft.ScrollMode.AUTO), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Сохранить", on_click=save)])
        page.show_dialog(dialog)

    draw()
    return root
