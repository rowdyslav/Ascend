from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "ascend"
    default_user_id: str = "64b000000000000000000001"
    nutrition_goals: dict[str, float] = {
        "kcal": 2600, "protein_g": 180, "fat_g": 80, "carbs_g": 300,
        "fiber_g": 30, "water_ml": 2500,
    }
    completion_weights: dict[str, float] = {
        "protocol": 0.35, "workout": 0.25, "nutrition": 0.25, "checks": 0.15,
    }
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
