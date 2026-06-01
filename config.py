"""Central configuration. Reads from environment variables or a .env file.

Everything tunable lives here so there are no magic numbers buried in the code.
That matters for the interview: when they ask "where does the 15% come from?",
the answer is "one config value, BROKER_MAX_UPLIFT, documented in .env.example".
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Auth
    api_key: str = "dev-secret-key-change-me"

    # FMCSA
    fmcsa_webkey: str = ""
    use_mock_fmcsa: bool = True

    # Negotiation policy
    broker_max_uplift: float = 0.15
    max_negotiation_rounds: int = 3

    # Storage
    database_path: str = "data.db"


settings = Settings()
