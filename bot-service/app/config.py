from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_USER: str = "nexus_app"
    DB_PASSWORD: str = "app_secure_password_456"
    DB_NAME: str = "nexus_chat"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_secure_password_789"

    model_config = ConfigDict(extra="ignore")

settings = Settings()