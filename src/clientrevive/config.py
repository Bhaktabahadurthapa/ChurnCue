"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings; secrets are intentionally not supported."""

    model_config = SettingsConfigDict(env_prefix="CLIENTREVIVE_", env_file=".env", extra="ignore")

    # Binding all interfaces is required for the container boundary.
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    database_path: Path = Path("data/clientrevive.db")
    artifact_dir: Path = Path("data/artifacts")
    demo_data_path: Path = Path("data/demo/customer_churn_demo.csv")
    max_input_rows: int = Field(default=5_000, ge=1, le=50_000)
    max_demo_rows: int = Field(default=500, ge=1, le=5_000)
    max_string_length: int = Field(default=200, ge=16, le=2_000)
    random_state: int = 42


@lru_cache
def get_settings() -> Settings:
    return Settings()
