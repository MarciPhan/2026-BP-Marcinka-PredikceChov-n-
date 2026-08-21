from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    web_port: int = 8093
    environment: Literal["development", "test", "production"] = "development"
    use_fakeredis: bool = False
    
    activity_inactivity_threshold_days: int = 14
    event_retention_days: int = 90

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
