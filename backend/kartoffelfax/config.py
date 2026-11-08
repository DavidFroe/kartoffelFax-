"""Application configuration, loaded from environment / .env via pydantic-settings."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KARTOFFELFAX_", env_file=".env", extra="ignore")

    data_dir: Path = Path.home() / ".local" / "share" / "kartoffelfax"
    database_url: str = ""  # resolved to data_dir/kartoffelfax.db if left empty
    inbox_dir: str = "inbox"
    outbox_dir: str = "outbox"
    archive_dir: str = "archive"
    uploads_dir: str = "uploads"
    log_level: str = "INFO"
    secret_key: str = ""  # Fernet key; if empty, generated once and stored in data_dir/secret.key

    def resolved_database_path(self) -> Path:
        if self.database_url:
            return Path(self.database_url)
        return self.data_dir / "kartoffelfax.db"

    def ensure_directories(self) -> None:
        for sub in (self.inbox_dir, self.outbox_dir, self.archive_dir, self.uploads_dir):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)


settings = Settings()
