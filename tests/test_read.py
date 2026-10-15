from __future__ import annotations

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

from agent_team_mail.config import Settings
from agent_team_mail.read import read_bot_mail


def _message(sender: str, subject: str, body: str, message_id: str) -> bytes:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = "agent@example.com"
    message["Subject"] = subject
    message["Date"] = "Thu, 15 Oct 2026 10:00:00 +0000"
    message["Message-ID"] = message_id
    message.set_content(body)
    return message.as_bytes()


def test_filters_non_team_senders_without_marking_them_read(settings: Settings) -> None:
    imap = MagicMock()
    imap.select.return_value = ("OK", [b"2"])
    imap.search.return_value = ("OK", [b"1 2"])
    messages = {
        b"1": _message("stranger@outside.example", "Ignore", "Not allowed", "<one@example>"),
        b"2": _message("Alice <alice@example.com>", "Reply", "Approved", "<two@example>"),
    }
    imap.fetch.side_effect = lambda number, _item: ("OK", [(b"data", messages[number])])
    imap.store.return_value = ("OK", [])

    with patch("agent_team_mail.read.imaplib.IMAP4_SSL", return_value=imap):
        result = read_bot_mail(settings, unread_only=True, mark_read=True)

    assert result == {
        "messages": [
            {
                "sender": "alice@example.com",
                "subject": "Reply",
                "date": "Thu, 15 Oct 2026 10:00:00 +0000",
                "body": "Approved",
                "message_id": "<two@example>",
            }
        ],
        "count": 1,
    }
    imap.search.assert_called_once_with(None, "UNSEEN")
    imap.store.assert_called_once_with(b"2", "+FLAGS", r"(\Seen)")


def test_since_filters_exact_timestamp_and_uses_peek(settings: Settings) -> None:
    imap = MagicMock()
    imap.select.return_value = ("OK", [])
    imap.search.return_value = ("OK", [b"1"])
    imap.fetch.return_value = (
        "OK",
        [
            (
                b"data",
                _message("alice@example.com", "Earlier", "Old", "<old@example>"),
            )
        ],
    )

    with patch("agent_team_mail.read.imaplib.IMAP4_SSL", return_value=imap):
        result = read_bot_mail(
            settings,
            unread_only=False,
            since="2026-10-15T12:00:00Z",
            mark_read=True,
        )

    assert result == {"messages": [], "count": 0}
    imap.search.assert_called_once_with(None, "SINCE", "15-Oct-2026")
    imap.fetch.assert_called_once_with(b"1", "(BODY.PEEK[])")
    imap.store.assert_not_called()


def test_rejects_out_of_range_limit(settings: Settings) -> None:
    with patch("agent_team_mail.read.imaplib.IMAP4_SSL") as imap:
        try:
            read_bot_mail(settings, limit=101)
        except ValueError as exc:
            assert str(exc) == "limit must be between 1 and 100"
        else:
            raise AssertionError("expected ValueError")
    imap.assert_not_called()
