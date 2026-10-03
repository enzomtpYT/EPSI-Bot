"""Configuration management using environment variables."""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_INSECURE_SECRET = "epsi-bot-super-secret-key-change-in-production"
_raw_secret = os.getenv("SESSION_SECRET", "").strip()
if not _raw_secret or _raw_secret == DEFAULT_INSECURE_SECRET:
    logger.warning(
        "SESSION_SECRET is unset or using default insecure placeholder. "
        "Generating a cryptographically secure random key for session security."
    )
    _effective_session_secret = secrets.token_hex(32)
else:
    _effective_session_secret = _raw_secret


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

    # Web & OAuth2 settings
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "8080"))
    web_base_url: str = os.getenv("WEB_BASE_URL", "http://localhost:8080")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    discord_client_secret: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    discord_redirect_uri: str = os.getenv(
        "DISCORD_REDIRECT_URI", "http://localhost:8080/auth/callback"
    )
    discord_oauth_scopes: str = os.getenv("DISCORD_OAUTH_SCOPES", "identify applications.commands")
    discord_oauth_integration_type: str = os.getenv("DISCORD_OAUTH_INTEGRATION_TYPE", "1")
    session_secret: str = _effective_session_secret

    @property
    def effective_discord_client_id(self) -> str:
        """Return the configured Discord client ID or default fallback."""
        default_id = "1357424188306227451"
        return self.discord_client_id.strip() if self.discord_client_id else default_id

    @property
    def bot_invite_url(self) -> str:
        """Return OAuth2 authorize link with permissions to add the bot to Discord."""
        return (
            f"https://discord.com/oauth2/authorize?client_id={self.effective_discord_client_id}"
            f"&permissions=2048&scope=bot%20applications.commands"
        )

    @property
    def sqlite_database_url(self) -> str:
        """Return fallback SQLite connection string."""
        db_file = Path(self.sqlite_path).resolve()
        db_file.parent.mkdir(parents=True, exist_ok=True)
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
