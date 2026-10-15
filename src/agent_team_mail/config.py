"""Environment-based configuration for agent-team-mail."""

from __future__ import annotations

import os
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when server configuration is missing or invalid."""


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _port(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if not 1 <= value <= 65535:
        raise ConfigError(f"{name} must be between 1 and 65535")
    return value


def _email(value: str, name: str) -> str:
    display_name, address = parseaddr(value)
    if display_name or address != value or "@" not in address:
        raise ConfigError(f"{name} must contain a plain email address")
    local, domain = address.rsplit("@", 1)
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ConfigError(f"{name} contains an invalid email address")
    return address.lower()


def _csv(name: str, *, required: bool = False) -> tuple[str, ...]:
    values = tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())
    if required and not values:
        raise ConfigError(f"{name} must contain at least one value")
    return values


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated runtime settings."""

    bind_host: str
    port: int
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int
    bot_address: str
    mail_username: str
    mail_app_password: str
    team_addresses: tuple[str, ...]
    sent_folder: str
    allowed_hosts: tuple[str, ...]

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> Settings:
        """Load settings from an optional dotenv file and then the environment."""
        if env_file:
            path = Path(env_file)
            if not path.is_file():
                raise ConfigError(f"Environment file not found: {path}")
            load_dotenv(path, override=False)

        bind_host = os.getenv("BIND_HOST", "127.0.0.1").strip()
        if not bind_host:
            raise ConfigError("BIND_HOST cannot be empty")

        sent_folder = os.getenv("SENT_FOLDER", "Sent").strip()
        if not sent_folder:
            raise ConfigError("SENT_FOLDER cannot be empty")

        team = tuple(dict.fromkeys(_email(value, "TEAM_ADDRESSES") for value in _csv(
            "TEAM_ADDRESSES", required=True
        )))
        allowed_hosts = _csv("ALLOWED_HOSTS")

        return cls(
            bind_host=bind_host,
            port=_port("PORT", 8765),
            smtp_host=_required("SMTP_HOST"),
            smtp_port=_port("SMTP_PORT", 587),
            imap_host=_required("IMAP_HOST"),
            imap_port=_port("IMAP_PORT", 993),
            bot_address=_email(_required("BOT_ADDRESS"), "BOT_ADDRESS"),
            mail_username=_required("MAIL_USERNAME"),
            mail_app_password=_required("MAIL_APP_PASSWORD"),
            team_addresses=team,
            sent_folder=sent_folder,
            allowed_hosts=allowed_hosts,
        )
