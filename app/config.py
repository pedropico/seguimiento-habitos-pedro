from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = "Ubicada en .env"
    DATABASE_URL: str = "sqlite:///./habitos.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEMO_USER_EMAIL: str = "demo@ejemplo.com"
    MCP_ISSUER_URL: str = "http://localhost:8000"


settings = Settings()
