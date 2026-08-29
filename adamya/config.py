"""Application settings loaded from environment variables or .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Runtime configuration shared by the API services."""

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5500"
    skyfield_data_dir: str = "./data"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        """Convert comma-separated origins into the list expected by CORS middleware."""
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cache settings so every request uses one consistent configuration object."""
    return Settings()

