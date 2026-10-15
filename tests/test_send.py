from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_team_mail.config import Settings
from agent_team_mail.send import send_to_team


def test_sends_only_to_configured_team_and_appends_copy(settings: Settings) -> None:
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    smtp.__exit__.return_value = False
    imap = MagicMock()
    imap.append.return_value = ("OK", [b"done"])

    with (
        patch("agent_team_mail.send.smtplib.SMTP", return_value=smtp),
        patch("agent_team_mail.send.imaplib.IMAP4_SSL", return_value=imap),
    ):
        result = send_to_team("Status update", "Everything is working.", settings)

    message = smtp.send_message.call_args.args[0]
    assert message["From"] == "agent@example.com"
    assert message["To"] == "alice@example.com, bob@example.com"
    assert message["Date"]
    assert message["Message-ID"]
    assert result["recipients"] == ["alice@example.com", "bob@example.com"]
    assert result["sent_copy"] is True
    imap.append.assert_called_once()
    assert imap.append.call_args.args[0] == "Sent"
    assert imap.append.call_args.args[1] == r"(\Seen)"


def test_sent_copy_failure_does_not_fail_send(
    settings: Settings,
    caplog,
) -> None:
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    smtp.__exit__.return_value = False

    with (
        patch("agent_team_mail.send.smtplib.SMTP", return_value=smtp),
        patch(
            "agent_team_mail.send.imaplib.IMAP4_SSL",
            side_effect=OSError("mailbox unavailable"),
        ),
    ):
        result = send_to_team("Status update", "The message still sends.", settings)

    smtp.send_message.assert_called_once()
    assert result["status"] == "sent"
    assert result["sent_copy"] is False
    assert "Sent-folder copy could not be saved" in caplog.text
    assert settings.mail_app_password not in caplog.text
