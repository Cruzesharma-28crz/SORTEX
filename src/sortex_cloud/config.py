from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://sortex:sortex@localhost:5432/sortex"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: Path = Path("./var/sortex")
    api_keys_json: str = Field(default="{}", validation_alias="SORTEX_API_KEYS_JSON")
    max_upload_mb: int = 12
    model_confidence_threshold: float = 0.65
    @property
    def api_keys(self) -> dict:
        import json
        value = json.loads(self.api_keys_json)
        if not isinstance(value, dict): raise ValueError("SORTEX_API_KEYS_JSON must be a JSON object")
        return value

@lru_cache
def get_settings() -> Settings:
    value = Settings()
    value.storage_root.mkdir(parents=True, exist_ok=True)
    return value
