"""Read and filter the bot inbox."""

from __future__ import annotations

import imaplib
from datetime import datetime
from email import message_from_bytes, policy
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any

from .config import Settings


def _parse_since(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("since must be an ISO 8601 date or datetime") from exc
    return parsed


def _plain_text(message: Message) -> str:
    if message.is_multipart():
        parts: list[str] = []
        for part in message.walk():
            if (
                part.get_content_type() == "text/plain"
                and part.get_content_disposition() != "attachment"
            ):
                parts.append(part.get_content())
        return "\n".join(part.strip() for part in parts if part.strip())
    if message.get_content_type() == "text/plain":
        return message.get_content().strip()
    return ""


def _sender(message: Message) -> str | None:
    addresses = getaddresses(message.get_all("From", []))
    if len(addresses) != 1:
        return None
    return addresses[0][1].lower()


def read_bot_mail(
    settings: Settings,
    *,
    limit: int = 20,
    unread_only: bool = True,
    since: str | None = None,
    mark_read: bool = False,
) -> dict[str, Any]:
    """Return inbox messages whose From address is in the fixed team allowlist."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    since_at = _parse_since(since)

    client = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    try:
        client.login(settings.mail_username, settings.mail_app_password)
        status, _ = client.select("INBOX")
        if status != "OK":
            raise RuntimeError("Could not select INBOX")

        criteria: list[str] = []
        if unread_only:
            criteria.append("UNSEEN")
        if since_at:
            criteria.extend(("SINCE", since_at.strftime("%d-%b-%Y")))
        status, data = client.search(None, *(criteria or ["ALL"]))
        if status != "OK":
            raise RuntimeError("Could not search INBOX")

        message_ids = data[0].split()
        results: list[dict[str, str]] = []
        allowed = set(settings.team_addresses)
        for message_number in reversed(message_ids):
            status, fetched = client.fetch(message_number, "(BODY.PEEK[])")
            if status != "OK" or not fetched:
                continue
            raw = next(
                (item[1] for item in fetched if isinstance(item, tuple) and len(item) > 1),
                None,
            )
            if not isinstance(raw, bytes):
                continue
            message = message_from_bytes(raw, policy=policy.default)
            sender = _sender(message)
            if sender not in allowed:
                continue

            if since_at:
                try:
                    message_date = parsedate_to_datetime(message.get("Date", ""))
                    comparable_since = since_at
                    if message_date.tzinfo is None and since_at.tzinfo is not None:
                        message_date = message_date.replace(tzinfo=since_at.tzinfo)
                    elif message_date.tzinfo is not None and since_at.tzinfo is None:
                        comparable_since = since_at.replace(tzinfo=message_date.tzinfo)
                    if message_date < comparable_since:
                        continue
                except (TypeError, ValueError):
                    pass

            if mark_read:
                client.store(message_number, "+FLAGS", r"(\Seen)")
            results.append(
                {
                    "sender": sender,
                    "subject": str(message.get("Subject", "")),
                    "date": str(message.get("Date", "")),
                    "body": _plain_text(message),
                    "message_id": str(message.get("Message-ID", "")),
                }
            )
            if len(results) >= limit:
                break

        return {"messages": results, "count": len(results)}
    finally:
        try:
            client.logout()
        except Exception:  # noqa: BLE001, S110 - preserve the original operation result
            pass
