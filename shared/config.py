from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    web_port: int = 8093
    environment: Literal["development", "test", "production"] = "development"
    use_fakeredis: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
