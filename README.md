# agent-team-mail

`agent-team-mail` is a small, open-source [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives AI agents a safe way to email a fixed group of people and read their replies.

The server owns the mailbox credentials. Agents receive only two narrow tools: send a message to the whole configured team, or read replies from configured team members. There is deliberately no recipient argument.

## Why this design?

Giving an agent normal email credentials also gives it the ability to contact arbitrary recipients and access unrelated mail. This server reduces that authority:

- recipients are a server-side allowlist and cannot be overridden by a tool call;
- inbox results are filtered to messages from that same allowlist;
- mailbox credentials never enter MCP tool inputs or outputs;
- HTTP binds to localhost by default;
- MCP DNS-rebinding protection validates the HTTP `Host` header;
- remote access is intended to pass through an authenticated tunnel such as Cloudflare Access.

This is a guardrail, not a complete security boundary. Run it with a dedicated mailbox, a dedicated operating-system user, minimal network exposure, and provider-supported app credentials.

## Features

- Streamable HTTP MCP at `/mcp` and local stdio MCP
- SMTP submission using STARTTLS on port 587 by default
- IMAP access using TLS on port 993 by default
- best-effort archival of outbound messages in the IMAP Sent folder
- plain-text inbox results with optional unread, date, and mark-read controls
- environment, dotenv, systemd, Docker Compose, and tunnel examples

## Quick start

Python 3.11 or newer is required.

```bash
git clone https://github.com/Ojisan1/agent-team-mail.git
cd agent-team-mail
python -m venv .venv
. .venv/bin/activate
python -m pip install .
cp .env.example .env
chmod 600 .env
```

Edit `.env` with a dedicated mailbox, an app password, and the team addresses. Then start the local HTTP server:

```bash
agent-team-mail --env-file .env
```

The MCP endpoint is `http://127.0.0.1:8765/mcp`. For stdio instead:

```bash
agent-team-mail --env-file .env --transport stdio
```

See [client examples](docs/clients.md), the [Cloudflare Tunnel guide](docs/cloudflare-tunnel.md), or the included [systemd unit](deploy/agent-team-mail.service). To use Docker:

```bash
docker compose up --build -d
```

Compose publishes the service on the host's loopback interface only.

## Configuration

Values come from the process environment. `--env-file PATH` loads a dotenv file without overriding variables already present in the environment.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BIND_HOST` | No | `127.0.0.1` | HTTP listening address |
| `PORT` | No | `8765` | HTTP listening port |
| `SMTP_HOST` | Yes | — | SMTP submission hostname |
| `SMTP_PORT` | No | `587` | SMTP STARTTLS port |
| `IMAP_HOST` | Yes | — | IMAP hostname |
| `IMAP_PORT` | No | `993` | IMAP-over-TLS port |
| `BOT_ADDRESS` | Yes | — | Address placed in the message `From` header |
| `MAIL_USERNAME` | Yes | — | SMTP and IMAP login name |
| `MAIL_APP_PASSWORD` | Yes | — | Dedicated mailbox app password |
| `TEAM_ADDRESSES` | Yes | — | Comma-separated fixed allowlist |
| `SENT_FOLDER` | No | `Sent` | IMAP mailbox for outbound copies |
| `ALLOWED_HOSTS` | No | local hosts | Comma-separated HTTP `Host` patterns accepted by MCP protection |

Email values must be plain addresses such as `alice@example.com`, not display-name forms. When `ALLOWED_HOSTS` is omitted, only `127.0.0.1:*`, `localhost:*`, and `[::1]:*` are accepted. If a reverse proxy cannot preserve a local Host header, explicitly add only its expected hostname and port.

Do not commit `.env`; repository ignore rules exclude environment files.

## MCP tools

### `send_to_team`

Input:

```json
{
  "subject": "Deployment complete",
  "body": "The service is healthy. Please reply if you see an issue."
}
```

There is no recipient field. The server sends to every address in `TEAM_ADDRESSES`.

Example output:

```json
{
  "status": "sent",
  "recipients": ["alice@example.com", "bob@example.com"],
  "message_id": "<generated-id@example.com>",
  "sent_copy": true
}
```

### `read_bot_mail`

Input:

```json
{
  "limit": 20,
  "unread_only": true,
  "since": "2026-10-15T00:00:00Z",
  "mark_read": false
}
```

- `limit` is from 1 to 100.
- `unread_only` searches only unseen messages.
- `since` accepts an ISO 8601 date or datetime and is optional.
- `mark_read` marks only returned, allowlisted messages as seen.

Example output:

```json
{
  "messages": [
    {
      "sender": "alice@example.com",
      "subject": "Re: Deployment complete",
      "date": "Thu, 15 Oct 2026 12:30:00 +0000",
      "body": "Confirmed. Everything looks good.",
      "message_id": "<reply-id@example.com>"
    }
  ],
  "count": 1
}
```

HTML-only messages have an empty `body`; attachments are not returned.

## Sent-folder behavior

Each outbound message gets `Date` and `Message-ID` headers. After SMTP accepts it, the server uses IMAP `APPEND` to save the exact message in `SENT_FOLDER` with the `\Seen` flag.

Archival is intentionally best effort. If the folder name is wrong, permissions are missing, or IMAP is temporarily unavailable, the tool still reports the successful send with `"sent_copy": false` and logs a warning. It does not retry the SMTP send, preventing an archival problem from creating duplicate email.

## Troubleshooting

- **`421 Invalid Host header`**: the incoming `Host` header is not in `ALLOWED_HOSTS`. With Cloudflare Tunnel, set the route's HTTP Host Header to `localhost:8765`; see the [tunnel guide](docs/cloudflare-tunnel.md).
- **SMTP authentication or STARTTLS error**: confirm the provider's submission hostname, port, app-password support, and SMTP access.
- **IMAP login or read error**: enable IMAP for the dedicated mailbox and verify the IMAP hostname and app password.
- **`sent_copy` is false**: check the service log and verify `SENT_FOLDER`. Common folder names vary by mailbox language and provider.
- **No replies returned**: the exact parsed sender address must occur in `TEAM_ADDRESSES`. Check `unread_only` and `since`, too.
- **Dotenv appears ignored**: existing process environment values intentionally take precedence over the file.

Logs never intentionally include credentials. Treat logs and email contents as sensitive operational data anyway.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
