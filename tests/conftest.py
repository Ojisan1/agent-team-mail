from __future__ import annotations

import pytest

from agent_team_mail.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        bind_host="127.0.0.1",
        port=8765,
        smtp_host="mail.example.com",
        smtp_port=587,
        imap_host="mail.example.com",
        imap_port=993,
        bot_address="agent@example.com",
        mail_username="agent@example.com",
        mail_app_password="placeholder-password",
        team_addresses=("alice@example.com", "bob@example.com"),
        sent_folder="Sent",
        allowed_hosts=(),
    )
