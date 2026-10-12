from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # where the backend lives: localhost when running on the laptop,
    # http://api_app:8080 inside docker compose (set in docker-compose.yml)
    api_url: str = "http://localhost:8080"

    site_name: str = "The Daily Draft"
    site_tagline: str = "Stories, notes and half-finished ideas from our writers."

    # the backend's JWT expires after 30 minutes, the cookie holding it shouldn't outlive it
    token_max_age_minutes: int = 30
    # True once the site is served over https, then the browser only sends the cookie over https
    cookie_secure: bool = False


settings = Settings()
