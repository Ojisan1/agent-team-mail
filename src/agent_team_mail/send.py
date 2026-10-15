"""Outbound mail with fixed recipients and best-effort Sent-folder archival."""

from __future__ import annotations

import imaplib
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Any

from .config import Settings

logger = logging.getLogger(__name__)


def _append_sent_copy(message: EmailMessage, settings: Settings) -> bool:
    client: imaplib.IMAP4_SSL | None = None
    try:
        client = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        client.login(settings.mail_username, settings.mail_app_password)
        status, _ = client.append(
            settings.sent_folder,
            r"(\Seen)",
            None,
            message.as_bytes(),
        )
        if status != "OK":
            raise RuntimeError(f"IMAP APPEND returned {status}")
        return True
    except Exception as exc:  # noqa: BLE001 - archival must never fail a successful send
        logger.warning("Message sent, but its Sent-folder copy could not be saved: %s", exc)
        return False
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:  # noqa: BLE001, S110 - best-effort connection cleanup
                pass


def send_to_team(subject: str, body: str, settings: Settings) -> dict[str, Any]:
    """Send one plain-text message to every configured team address."""
    if not subject.strip():
        raise ValueError("subject cannot be empty")
    if not body.strip():
        raise ValueError("body cannot be empty")

    message = EmailMessage()
    message["From"] = settings.bot_address
    message["To"] = ", ".join(settings.team_addresses)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=settings.bot_address.rsplit("@", 1)[1])
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as client:
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
        client.login(settings.mail_username, settings.mail_app_password)
        client.send_message(message)

    sent_copy = _append_sent_copy(message, settings)
    return {
        "status": "sent",
        "recipients": list(settings.team_addresses),
        "message_id": message["Message-ID"],
        "sent_copy": sent_copy,
    }
