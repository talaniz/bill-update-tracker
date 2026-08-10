from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    congress_api_key: str | None = None
    congress_api_key_file: str | None = None
    database_url: str = "postgresql://tracker:tracker@localhost:5432/bill_update_tracker"
    tracker_timezone: str = "America/Los_Angeles"
    poll_interval_seconds: int = 3600
    initial_lookback_days: int = 0
    enable_scheduler: bool = True

    def resolved_congress_api_key(self) -> str | None:
        if self.congress_api_key_file:
            secret_path = Path(self.congress_api_key_file)
            if secret_path.exists():
                return secret_path.read_text().strip()
        return self.congress_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
