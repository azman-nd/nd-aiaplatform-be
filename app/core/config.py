from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional
from pydantic import Extra, computed_field

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Agent Platform"
    
    # Environment
    ENVIRONMENT: str
    
    # Database settings
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: str
    DB_HOST: str
    DB_SCHEMA: str = "aiaplatform"

    model_config = {
        "extra": "allow"
    }

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?options=-c%20search_path%3D{self.DB_SCHEMA}"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
