from datetime import date, timedelta

import flet as ft

from api_client import ApiClient, ApiError
from components.card import card, section_title
from components.charts import line_chart
from components.progress import ProgressBar
from components.sheets import show_bottom_sheet
from theme import ACCENT, ERROR, PURPLE, SUCCESS, TEXT_SECONDARY, WARNING

MEALS = [("breakfast", "Завтрак"), ("lunch", "Обед"), ("dinner", "Ужин"), ("snack", "Перекусы"), ("drinks", "Напитки")]
PERIODS = [(7, "7 дней"), (30, "30 дней"), (90, "90 дней")]
BASE_GOALS = {"kcal": 2600, "protein_g": 180, "fat_g": 80, "carbs_g": 300, "fiber_g": 30, "water_ml": 2500}

# Flet 0.86 has no persistent client storage, so favourites and recipes live in
# memory for the lifetime of the app session.
_FAVORITES: dict[str, dict] = {}
_RECIPES: dict[str, dict] = {}


def goals_for(day_type: str) -> dict[str, float]:
    goals = dict(BASE_GOALS)
    if day_type == "rest":
        goals["kcal"] *= 0.85
    elif day_type == "refeed":
        goals["kcal"] *= 1.1
        goals["carbs_g"] *= 1.25
    return goals


def nutrition_screen(page: ft.Page, api: ApiClient, navigate) -> ft.Control:
    selected_day = date.today()
    period_days = 7
    root = ft.Column(expand=True)
    recent_foods: list[dict] = []

    def notify(text: str, bad: bool = False) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(text), bgcolor=ERROR if bad else SUCCESS))

    def store_get(key: str, default):
        source = _FAVORITES if key == "ascend_favorites" else _RECIPES
        return dict(source) or default

    def store_set(key: str, value) -> None:
        target = _FAVORITES if key == "ascend_favorites" else _RECIPES
        target.clear()
        target.update(value)

    def draw() -> None:
        nonlocal recent_foods
        root.controls.clear()
        try:
            summary = api.get("/nutrition/daily-summary", {"date": selected_day.isoformat()})
            current_meals = {item["meal_type"]: item for item in api.get("/meals", {"date": selected_day.isoformat()})}
        except ApiError as exc:
            root.controls.append(ft.Text(str(exc)))
            page.update()
            return
        try:
            day_info = api.get(f"/days/{selected_day.isoformat()}")
            day_type = day_info["day"].get("day_type") or "training"
        except ApiError:
            day_type = "training"
        goals = goals_for(day_type)

        # Recents: foods already used today (for the picker quick tab).
        recent_foods = []
        for meal in current_meals.values():
            try:
                entries = api.get(f"/meals/{meal['id']}/entries")
            except ApiError:
                continue
            for entry in entries:
                food = entry.get("food") or {}
                if food.get("id") and food["id"] not in {item["id"] for item in recent_foods}:
                    recent_foods.append({"id": food["id"], "name": food["name"], "kcal": (entry["nutrients"].get("kcal") or 0)})

        view = ft.ListView(expand=True, spacing=12, padding=16)
        view.controls.append(section_title("Питание", ft.Text(f"{selected_day.strftime('%d.%m.%Y')} · {day_type}", color=TEXT_SECONDARY)))

        progress_rows = []
        labels = [("Калории", "kcal", "ккал"), ("Белки", "protein_g", "г"), ("Жиры", "fat_g", "г"), ("Углеводы", "carbs_g", "г"), ("Клетчатка", "fiber_g", "г"), ("Вода", "water_ml", "мл")]
        for label, key, unit in labels:
            fact = summary["totals"].get(key) or 0
            goal = goals.get(key, 0)
            over = fact > goal if goal else False
            progress_rows.append(ft.Column([
                ft.Row([ft.Text(label), ft.Text(f"{fact:.0f} / {goal:.0f} {unit}", color=WARNING if over else TEXT_SECONDARY, expand=True, text_align=ft.TextAlign.RIGHT)]),
                ProgressBar(fact, goal, over_color=(WARNING if over else ACCENT)),
            ], spacing=4))
        view.controls.append(card(section_title("Дневные цели"), *progress_rows))

        # Per-nutrient breakdown: fact / goal / remaining / %.
        breakdown_rows = []
        for label, key, unit in labels:
            fact = summary["totals"].get(key) or 0
            goal = goals.get(key, 0)
            remaining = max(0, goal - fact)
            percent = round(fact / goal * 100, 1) if goal else 0
            color = WARNING if goal and fact > goal else (SUCCESS if goal and percent >= 90 else TEXT_SECONDARY)
            breakdown_rows.append(ft.Row([
                ft.Text(label, width=80, size=12, color=TEXT_SECONDARY),
                ft.Text(f"{fact:.0f}", size=12, expand=True),
                ft.Text(f"{goal:.0f}", size=12, expand=True),
                ft.Text(f"{remaining:.0f}", size=12, expand=True),
                ft.Text(f"{percent:.0f}%", size=12, color=color, width=44, text_align=ft.TextAlign.RIGHT),
            ]))
        view.controls.append(card(
            section_title("Раскладка по нутриентам"),
            ft.Row([ft.Text("", width=80), ft.Text("Факт", size=11, color=TEXT_SECONDARY, expand=True), ft.Text("Цель", size=11, color=TEXT_SECONDARY, expand=True), ft.Text("Осталось", size=11, color=TEXT_SECONDARY, expand=True), ft.Text("%", size=11, color=TEXT_SECONDARY, width=44, text_align=ft.TextAlign.RIGHT)]),
            *breakdown_rows,
        ))

        for meal_type, label in MEALS:
            meal = current_meals.get(meal_type)
            rows = []
            if meal:
                try:
                    entries = api.get(f"/meals/{meal['id']}/entries")
                except ApiError:
                    entries = []
                for entry in entries:
                    food = entry.get("food") or {"name": "Удалённый продукт"}
                    nutrients = entry["nutrients"]
                    rows.append(ft.Row([
                        ft.Column([ft.Text(food["name"], weight=ft.FontWeight.W_500), ft.Text(f"{entry['weight_g']:.0f} г · {nutrients['kcal']:.0f} ккал · Б {nutrients['protein_g']:.1f}/Ж {nutrients['fat_g']:.1f}/У {nutrients['carbs_g']:.1f}", size=12, color=TEXT_SECONDARY)], expand=True),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Удалить", on_click=lambda _, item=entry: delete_entry(item)),
                    ]))
            else:
                entries = []
            actions = ft.Row([
                ft.IconButton(ft.Icons.ADD, icon_color=ACCENT, tooltip="Добавить продукт", on_click=lambda _, kind=meal_type: add_food(kind)),
                ft.IconButton(ft.Icons.BOOKMARK_ADD_OUTLINED, icon_color=PURPLE, tooltip="Сохранить как рецепт", on_click=lambda _, kind=meal_type: save_recipe(kind), disabled=not entries),
            ])
            view.controls.append(card(section_title(label, actions), *(rows or [ft.Text("Пока пусто", color=TEXT_SECONDARY)])))

        view.controls.append(ft.OutlinedButton("Копировать приёмы с другой даты", icon=ft.Icons.CONTENT_COPY, on_click=copy_from_date))

        recipes = store_get("ascend_recipes", {})
        if recipes:
            recipe_rows = []
            for name, recipe in recipes.items():
                recipe_rows.append(ft.Row([
                    ft.Column([ft.Text(name, weight=ft.FontWeight.W_500), ft.Text(f"{len(recipe['entries'])} позиций · {recipe['meal_type']}", size=12, color=TEXT_SECONDARY)], expand=True),
                    ft.IconButton(ft.Icons.ADD, icon_color=ACCENT, tooltip="Добавить в приём", on_click=lambda _, value=name: apply_recipe(value)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Удалить рецепт", on_click=lambda _, value=name: delete_recipe(value)),
                ]))
            view.controls.append(card(section_title("Мои рецепты"), *recipe_rows))

        # Charts with period toggle.
        # ВАЖНО (flet 0.86): selected должен быть list, а не set —
        # set не сериализуется в msgpack и роняет всю flet-сессию.
        periods = ft.Row([
            ft.SegmentedButton(
                selected=[str(period_days)],
                segments=[ft.Segment(value=str(days), label=ft.Text(text)) for days, text in PERIODS],
                on_change=choose_period,
                show_selected_icon=False,
            ),
        ])
        view.controls.append(card(section_title("Графики", periods), charts_view()))

        root.controls.append(view)
        page.update()

    def charts_view() -> ft.Control:
        try:
            end = selected_day
            start = end - timedelta(days=period_days - 1)
            trends = api.get("/analytics/nutrition", {"from": start.isoformat(), "to": end.isoformat()})
            rows = trends["daily"]
            if not rows:
                return ft.Text("Нет данных за период", color=TEXT_SECONDARY)
            averages = trends["averages"]
            over_count = len(trends["over_calorie_days"])
            return ft.Column([
                ft.Text(f"Среднее: {averages['kcal']:.0f} ккал · Б {averages['protein_g']:.0f} / Ж {averages['fat_g']:.0f} / У {averages['carbs_g']:.0f} г", color=TEXT_SECONDARY, size=12),
                ft.Text(f"Дней выше лимита калорий: {over_count}", color=WARNING if over_count else SUCCESS, size=12),
                line_chart({"Ккал": [row["kcal"] for row in rows], "Белок": [row["protein_g"] for row in rows], "Жиры": [row["fat_g"] for row in rows], "Углеводы": [row["carbs_g"] for row in rows]}, [str(row["date"])[5:] for row in rows]),
            ], spacing=6)
        except ApiError:
            return ft.Text("Не удалось загрузить графики", color=TEXT_SECONDARY)

    def choose_period(event: ft.ControlEvent) -> None:
        nonlocal period_days
        period_days = int(event.control.selected[0])
        draw()

    def delete_entry(entry: dict) -> None:
        try:
            api.delete(f"/entries/{entry['id']}")
            draw()
        except ApiError as exc:
            notify(str(exc), True)

    def add_food(meal_type: str) -> None:
        search = ft.TextField(label="Поиск продукта", autofocus=True)
        results = ft.Column(scroll=ft.ScrollMode.AUTO, height=250)
        mode = {"value": "search"}

        def food_row(food: dict) -> ft.Control:
            favorites = store_get("ascend_favorites", {})
            is_fav = food["id"] in favorites
            return ft.Row([
                ft.ListTile(
                    title=ft.Text(food["name"]),
                    subtitle=ft.Text(f"{food['per_100g']['kcal']:.0f} ккал / 100 г" if "per_100g" in food else f"{food['kcal']:.0f} ккал"),
                    on_click=lambda _, item=food: choose(item),
                    expand=True,
                ),
                ft.IconButton(
                    ft.Icons.STAR if is_fav else ft.Icons.STAR_BORDER,
                    icon_color=WARNING if is_fav else TEXT_SECONDARY,
                    tooltip="В избранное",
                    on_click=lambda _, item=food: toggle_favorite(item),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        def render_results() -> None:
            if mode["value"] == "search":
                try:
                    foods = api.get("/foods/search", {"q": search.value or ""})
                    results.controls = [food_row(food) for food in foods]
                except ApiError as exc:
                    notify(str(exc), True)
            elif mode["value"] == "favorites":
                favorites = store_get("ascend_favorites", {})
                results.controls = [food_row(food) for food in favorites.values()] or [ft.Text("Избранных нет — нажмите ★ у продукта", color=TEXT_SECONDARY)]
            else:
                results.controls = [food_row({"id": food["id"], "name": food["name"], "kcal": food["kcal"]}) for food in recent_foods] or [ft.Text("Сегодня ещё ничего не ели", color=TEXT_SECONDARY)]
            page.update()

        def switch_mode(value: str) -> None:
            mode["value"] = value
            render_results()

        def toggle_favorite(food: dict) -> None:
            favorites = store_get("ascend_favorites", {})
            if food["id"] in favorites:
                favorites.pop(food["id"])
            else:
                favorites[food["id"]] = {"id": food["id"], "name": food["name"], "per_100g": food.get("per_100g", {"kcal": food.get("kcal", 0), "protein_g": 0, "fat_g": 0, "carbs_g": 0})}
            store_set("ascend_favorites", favorites)
            render_results()

        def choose(food: dict) -> None:
            grams = ft.TextField(label="Вес, г", value="100", keyboard_type=ft.KeyboardType.NUMBER)

            def save(_: ft.ControlEvent) -> None:
                try:
                    meal = api.post("/meals", {"date": selected_day.isoformat(), "meal_type": meal_type})
                    api.post(f"/meals/{meal['id']}/entries", {"food_id": food["id"], "weight_g": float(grams.value)})
                    page.pop_dialog()
                    page.pop_dialog()
                    draw()
                except (TypeError, ValueError, ApiError) as exc:
                    notify(str(exc), True)

            weight_sheet = ft.Column([ft.Text(food["name"], size=18, weight=ft.FontWeight.BOLD), ft.Text("Нутриенты будут пересчитаны под вес порции автоматически.", size=12, color=TEXT_SECONDARY), grams, ft.FilledButton("Добавить", on_click=save, height=48)], tight=True)
            show_bottom_sheet(page, weight_sheet)

        def manual(_: ft.ControlEvent) -> None:
            name = ft.TextField(label="Название")
            kcal = ft.TextField(label="Ккал / 100 г", keyboard_type=ft.KeyboardType.NUMBER)
            protein = ft.TextField(label="Белки / 100 г", keyboard_type=ft.KeyboardType.NUMBER, value="0")
            fat = ft.TextField(label="Жиры / 100 г", keyboard_type=ft.KeyboardType.NUMBER, value="0")
            carbs = ft.TextField(label="Углеводы / 100 г", keyboard_type=ft.KeyboardType.NUMBER, value="0")

            def create(_: ft.ControlEvent) -> None:
                try:
                    food = api.post("/foods", {"name": name.value, "per_100g": {"kcal": float(kcal.value), "protein_g": float(protein.value), "fat_g": float(fat.value), "carbs_g": float(carbs.value)}})
                    page.pop_dialog()
                    choose(food)
                except (TypeError, ValueError, ApiError) as exc:
                    notify(str(exc), True)

            dialog = ft.AlertDialog(title=ft.Text("Создать продукт"), content=ft.Column([name, kcal, protein, fat, carbs], tight=True), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Создать", on_click=create)])
            page.show_dialog(dialog)

        mode_buttons = ft.Row([
            ft.FilledTonalButton("Поиск", on_click=lambda _: switch_mode("search")),
            ft.FilledTonalButton("Избранные", on_click=lambda _: switch_mode("favorites")),
            ft.FilledTonalButton("Недавние", on_click=lambda _: switch_mode("recents")),
        ], scroll=ft.ScrollMode.AUTO)
        sheet_content = ft.Column([ft.Text("Добавить продукт", size=20, weight=ft.FontWeight.BOLD), mode_buttons, ft.Row([search, ft.IconButton(ft.Icons.SEARCH, on_click=lambda _: render_results())]), ft.TextButton("Создать вручную", on_click=manual), results], tight=True)
        show_bottom_sheet(page, sheet_content)
        render_results()

    def save_recipe(meal_type: str) -> None:
        name = ft.TextField(label="Название рецепта", autofocus=True)

        def save(_: ft.ControlEvent) -> None:
            if not name.value:
                notify("Введите название", True)
                return
            try:
                meals = {item["meal_type"]: item for item in api.get("/meals", {"date": selected_day.isoformat()})}
                meal = meals.get(meal_type)
                entries = api.get(f"/meals/{meal['id']}/entries") if meal else []
            except ApiError as exc:
                notify(str(exc), True)
                return
            recipes = store_get("ascend_recipes", {})
            recipes[name.value] = {"meal_type": meal_type, "entries": [{"food_id": entry["food_id"], "weight_g": entry["weight_g"], "name": (entry.get("food") or {}).get("name", "Продукт")} for entry in entries]}
            store_set("ascend_recipes", recipes)
            page.pop_dialog()
            notify("Рецепт сохранён")
            draw()

        dialog = ft.AlertDialog(title=ft.Text("Сохранить приём как рецепт"), content=ft.Column([name], tight=True), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Сохранить", on_click=save)])
        page.show_dialog(dialog)

    def apply_recipe(recipe_name: str) -> None:
        recipes = store_get("ascend_recipes", {})
        recipe = recipes.get(recipe_name)
        if not recipe:
            return
        try:
            meal = api.post("/meals", {"date": selected_day.isoformat(), "meal_type": recipe["meal_type"]})
            for entry in recipe["entries"]:
                api.post(f"/meals/{meal['id']}/entries", {"food_id": entry["food_id"], "weight_g": entry["weight_g"]})
            notify(f"Рецепт «{recipe_name}» добавлен")
            draw()
        except ApiError as exc:
            notify(str(exc), True)

    def delete_recipe(recipe_name: str) -> None:
        recipes = store_get("ascend_recipes", {})
        recipes.pop(recipe_name, None)
        store_set("ascend_recipes", recipes)
        draw()

    def copy_from_date(_: ft.ControlEvent) -> None:
        source_field = ft.TextField(label="Дата (ГГГГ-ММ-ДД)", value=(selected_day - timedelta(days=1)).isoformat())

        def run(_: ft.ControlEvent) -> None:
            try:
                source_day = date.fromisoformat(source_field.value)
            except ValueError:
                notify("Неверный формат даты", True)
                return
            try:
                source = api.get("/meals", {"date": source_day.isoformat()})
                copied = 0
                for source_meal in source:
                    destination = api.post("/meals", {"date": selected_day.isoformat(), "meal_type": source_meal["meal_type"]})
                    for entry in api.get(f"/meals/{source_meal['id']}/entries"):
                        api.post(f"/meals/{destination['id']}/entries", {"food_id": entry["food_id"], "weight_g": entry["weight_g"]})
                        copied += 1
                page.pop_dialog()
                notify(f"Скопировано записей: {copied}" if copied else "На эту дату приёмов нет")
                draw()
            except ApiError as exc:
                notify(str(exc), True)

        dialog = ft.AlertDialog(title=ft.Text("Копировать приёмы"), content=ft.Column([source_field], tight=True), actions=[ft.TextButton("Отмена", on_click=lambda _: page.pop_dialog()), ft.FilledButton("Копировать", on_click=run)])
        page.show_dialog(dialog)

    draw()
    return root
