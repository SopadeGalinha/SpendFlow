from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "SpendFlow API"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str

    if os.getenv("ENV", "development") == "production":
        model_config = SettingsConfigDict(extra="ignore")
    else:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
