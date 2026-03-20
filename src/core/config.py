from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    PROJECT_NAME: str = "SpendFlow API"
    DATABASE_URL: str
    SECRET_KEY: str = "SopinhadeGalinha"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Padrão Pydantic v2 para carregar o .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
