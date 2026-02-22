from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Weather Dashboard API"
    cache_ttl_seconds: int = 600
    http_timeout_seconds: int = 15  # timeout pentru requesturile HTTP

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()