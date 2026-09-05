from datetime import date, timedelta, time

from beanie import PydanticObjectId

from app.models import Exercise, Food, LabMarker, LabTest, Nutrients, ProtocolItem, Workout


FOODS = [
    ("Творог 2%", 81, 16.5, 2, 3), ("Куриная грудка", 113, 23.6, 1.9, 0),
    ("Гречка варёная", 110, 4.2, 1.1, 21.3), ("Рис варёный", 130, 2.7, .3, 28.2),
    ("Яйцо куриное", 157, 12.7, 11.5, .7), ("Банан", 96, 1.5, .5, 21),
    ("Овсянка", 366, 12, 6, 60), ("Лосось", 208, 20, 13, 0),
    ("Говядина постная", 187, 26, 9, 0), ("Картофель", 77, 2, .1, 17),
    ("Брокколи", 34, 2.8, .4, 6.6), ("Авокадо", 160, 2, 14.7, 8.5),
    ("Греческий йогурт", 59, 10, .4, 3.6), ("Хлеб цельнозерновой", 247, 13, 4.2, 41),
    ("Арахисовая паста", 588, 25, 50, 20), ("Оливковое масло", 884, 0, 100, 0),
    ("Яблоко", 52, .3, .2, 14), ("Тунец в собственном соку", 116, 26, 1, 0),
    ("Макароны твёрдых сортов", 131, 5, 1.1, 25), ("Кефир 1%", 40, 3, 1, 4),
]

# Extra micronutrients per food name (per 100 g), used to make progress bars meaningful.
FOOD_EXTRAS = {
    "Творог 2%": {"calcium_mg": 120},
    "Гречка варёная": {"fiber_g": 2.8, "magnesium_mg": 51},
    "Банан": {"fiber_g": 2.6, "potassium_mg": 358, "sugar_g": 12},
    "Овсянка": {"fiber_g": 8, "magnesium_mg": 129, "iron_mg": 3.6},
    "Брокколи": {"fiber_g": 2.6, "vit_c_mg": 89},
    "Авокадо": {"fiber_g": 6.7, "potassium_mg": 485},
    "Хлеб цельнозерновой": {"fiber_g": 7, "sodium_mg": 400},
    "Арахисовая паста": {"fiber_g": 6, "magnesium_mg": 168, "omega3_g": 0.03},
    "Яблоко": {"fiber_g": 2.4, "sugar_g": 10},
    "Лосось": {"omega3_g": 2.2, "vit_d_mcg": 11},
    "Яйцо куриное": {"saturated_fat_g": 3.3, "vit_b12_mcg": 0.9},
    "Говядина постная": {"iron_mg": 2.9, "zinc_mg": 4.8, "vit_b12_mcg": 2.1},
    "Кефир 1%": {"calcium_mg": 120, "vit_b2_mg": 0.17},
}


async def seed_database(user_id: PydanticObjectId) -> None:
    """Create a usable, entirely local starter dataset exactly once."""
    if await Food.count() == 0:
        for name, kcal, protein, fat, carbs in FOODS:
            extras = FOOD_EXTRAS.get(name, {})
            await Food(name=name, per_100g=Nutrients(kcal=kcal, protein_g=protein, fat_g=fat, carbs_g=carbs, **extras), source="seed").insert()
        # Water is logged as a food so that the water goal flows through the same nutrients pipeline.
        await Food(name="Вода", per_100g=Nutrients(water_ml=100), source="seed").insert()

    if await ProtocolItem.find(ProtocolItem.user_id == user_id).count() == 0:
        specs = [
            ("Миноксидил местно", "topical", 1, "ml", [time(8), time(20)], [], "topical"),
            ("Миноксидил", "drug", 2.5, "mg", [time(8)], [], "oral"),
            ("Тадалафил", "drug", 5, "mg", [time(9)], [], "oral"),
            ("Дутастерид", "drug", .5, "mg", [time(9)], [], "oral"),
            ("Омега-3", "supplement", 6, "capsule", [time(13)], [], "oral"),
            ("Магний", "supplement", 500, "mg", [time(22)], [], "oral"),
            ("Тестостерон", "injection", 225, "mg", [time(10)], [3, 7], "im"),
            ("Витамин D3", "supplement", 4000, "IU", [time(13)], [], "oral"),
        ]
        for name, category, value, unit, schedule, weekdays, route in specs:
            await ProtocolItem(
                user_id=user_id, name=name, category=category, planned_dose_value=value,
                planned_dose_unit=unit, schedule_times=schedule, weekdays=weekdays,
                route=route, start_date=date.today() - timedelta(days=30), stock_remaining=30,
            ).insert()

    if await Exercise.find(Exercise.user_id == user_id).count() == 0:
        specs = [
            ("Жим штанги лёжа", "грудь", "штанга"), ("Жим гантелей сидя", "плечи", "гантели"),
            ("Тяга верхнего блока", "спина", "блок"), ("Тяга штанги в наклоне", "спина", "штанга"),
            ("Приседания", "ноги", "штанга"), ("Румынская тяга", "ноги", "штанга"),
        ]
        for name, group, equipment in specs:
            await Exercise(user_id=user_id, name=name, muscle_group=group, equipment=equipment).insert()

    if await Workout.find(Workout.user_id == user_id).count() == 0:
        templates = [("Push", 0), ("Pull", 1), ("Legs", 2)]
        for name, offset in templates:
            await Workout(user_id=user_id, date=date.today() + timedelta(days=offset), name=name).insert()

    if await LabTest.find(LabTest.user_id == user_id).count() == 0:
        test = LabTest(user_id=user_id, date=date.today() - timedelta(days=14), panel_name="Гормоны и биохимия", lab="ASCEND Lab")
        await test.insert()
        markers = [
            ("гормоны", "Тестостерон", 28.1, "nmol/L", 8.6, 29),
            ("гормоны", "Эстрадиол", 108, "pmol/L", 40, 161),
            ("биохимия", "Ферритин", 92, "ng/mL", 30, 400),
            ("витамины", "Витамин D", 42, "ng/mL", 30, 100),
            ("ОАК", "Гемоглобин", 158, "g/L", 130, 170),
            ("биохимия", "АЛТ", 29, "U/L", 0, 41),
            ("биохимия", "АСТ", 26, "U/L", 0, 40),
            ("липиды", "Холестерин", 4.3, "mmol/L", 0, 5.2),
            ("липиды", "ЛПНП", 2.4, "mmol/L", 0, 3),
            ("биохимия", "Глюкоза", 4.8, "mmol/L", 3.9, 5.5),
        ]
        for category, name, value, unit, lo, hi in markers:
            await LabMarker(test_id=test.id, category=category, name=name, value=value, unit=unit, ref_min=lo, ref_max=hi, flag="normal").insert()
