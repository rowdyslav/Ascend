from datetime import date
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING


class Nutrients(BaseModel):
    """Embedded subdocument: Beanie 1.x embeds plain Pydantic models."""
    kcal: float = 0
    protein_g: float = 0
    fat_g: float = 0
    carbs_g: float = 0
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    calcium_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    vit_a_mcg: Optional[float] = None
    vit_c_mg: Optional[float] = None
    vit_d_mcg: Optional[float] = None
    vit_e_mg: Optional[float] = None
    vit_k_mcg: Optional[float] = None
    vit_b1_mg: Optional[float] = None
    vit_b2_mg: Optional[float] = None
    vit_b3_mg: Optional[float] = None
    vit_b5_mg: Optional[float] = None
    vit_b6_mg: Optional[float] = None
    vit_b9_mcg: Optional[float] = None
    vit_b12_mcg: Optional[float] = None
    omega3_g: Optional[float] = None
    water_ml: float = 0


class Food(Document):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    per_100g: Nutrients
    source: str = "manual"

    class Settings:
        name = "foods"
        indexes = ["name", "barcode"]


class Meal(Document):
    user_id: PydanticObjectId
    date: date
    meal_type: str

    class Settings:
        name = "meals"
        indexes = [IndexModel([("user_id", ASCENDING), ("date", ASCENDING), ("meal_type", ASCENDING)], unique=True)]


class FoodEntry(Document):
    meal_id: PydanticObjectId
    food_id: PydanticObjectId
    weight_g: float
    nutrients: Nutrients

    class Settings:
        name = "food_entries"
        indexes = ["meal_id"]
