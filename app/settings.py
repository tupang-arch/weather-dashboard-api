from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Weather Dashboard API"
    cache_ttl_seconds: int = 600  # 10 minutes

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()