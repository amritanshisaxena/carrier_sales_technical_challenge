from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = "dev-secret-key-change-me"
    database_url: str = ""
    happyrobot_api_key: str = ""
    happyrobot_use_case_id: str = ""


settings = Settings()
