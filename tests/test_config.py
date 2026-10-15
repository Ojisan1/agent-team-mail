from __future__ import annotations

import pytest

from agent_team_mail.config import ConfigError, Settings

REQUIRED = {
    "SMTP_HOST": "mail.example.com",
    "IMAP_HOST": "mail.example.com",
    "BOT_ADDRESS": "agent@example.com",
    "MAIL_USERNAME": "agent@example.com",
    "MAIL_APP_PASSWORD": "placeholder-password",
    "TEAM_ADDRESSES": "alice@example.com,bob@example.com,alice@example.com",
}


def _set_required(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)


def test_loads_defaults_and_deduplicates_team(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required(monkeypatch)

    settings = Settings.from_env()

    assert settings.bind_host == "127.0.0.1"
    assert settings.port == 8765
    assert settings.smtp_port == 587
    assert settings.imap_port == 993
    assert settings.team_addresses == ("alice@example.com", "bob@example.com")
    assert settings.sent_folder == "Sent"


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("TEAM_ADDRESSES", "", "TEAM_ADDRESSES"),
        ("BOT_ADDRESS", "Agent <agent@example.com>", "plain email address"),
        ("SMTP_PORT", "not-a-port", "integer"),
        ("IMAP_PORT", "70000", "between 1 and 65535"),
    ],
)
def test_rejects_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
    message: str,
) -> None:
    _set_required(monkeypatch)
    monkeypatch.setenv(name, value)

    with pytest.raises(ConfigError, match=message):
        Settings.from_env()


def test_environment_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_file = tmp_path / "mail.env"
    env_file.write_text(
        "\n".join(f"{key}={value}" for key, value in REQUIRED.items()) + "\nPORT=9000\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PORT", "8765")

    assert Settings.from_env(env_file).port == 8765
