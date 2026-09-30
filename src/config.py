"""Configuration management using environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Bot and Database environment settings."""

    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    postgres_db: str = os.getenv("POSTGRES_DB", "")
    postgres_user: str = os.getenv("POSTGRES_USER", "")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_host: str = os.getenv("POSTGRES_HOST", "")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    sqlite_path: str = os.getenv("SQLITE_PATH", "bot_data.sqlite3")
    timezone: str = os.getenv("BOT_TIMEZONE", "Europe/Paris")

    @property
    def sqlite_database_url(self) -> str:
        """Return fallback SQLite connection string."""
        db_file = Path(self.sqlite_path).resolve()
        return f"sqlite+aiosqlite:///{db_file}"

    @property
    def database_url(self) -> str:
        """Return async database connection string.

        Uses PostgreSQL with asyncpg if POSTGRES_HOST and credentials are set.
        Otherwise falls back to SQLite with aiosqlite.
        """
        if self.postgres_host and self.postgres_user and self.postgres_db:
            return (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self.sqlite_database_url


settings = Settings()
