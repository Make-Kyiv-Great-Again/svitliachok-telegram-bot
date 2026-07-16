from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    api_base_url: str = "http://localhost:8000/api/v1"
    db_file: str = "tokens.sqlite3"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
