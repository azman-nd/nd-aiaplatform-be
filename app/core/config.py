from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional
from pydantic import Extra, computed_field

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Agent Platform"
    
    # Environment
    ENVIRONMENT: str = "test"
    
    # Database settings
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_PORT: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_SCHEMA: str = "aiaplatform"

    model_config = {
        "extra": "allow"
    }

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        if all([self.DB_USER, self.DB_PASSWORD, self.DB_NAME, self.DB_PORT, self.DB_HOST]):
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?options=-c%20search_path%3D{self.DB_SCHEMA}"
        return "sqlite:///:memory:"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
