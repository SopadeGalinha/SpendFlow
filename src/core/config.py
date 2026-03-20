from pydantic_settings import BaseSettings  # type: ignore


class Settings(BaseSettings):
    PROJECT_NAME: str = "SpendFlow API"
    DATABASE_URL: str
    SECRET_KEY: str = "mudar-isso-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
