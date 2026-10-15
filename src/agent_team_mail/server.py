"""MCP server entry point."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .config import ConfigError, Settings
from .read import read_bot_mail as read_mail
from .send import send_to_team as send_mail


def create_server(settings: Settings) -> MCPServer:
    """Create an MCP server whose mail tools close over validated settings."""
    server = MCPServer(
        name="agent-team-mail",
        description="Send mail to a fixed team allowlist and read allowlisted replies.",
    )

    @server.tool(
        name="send_to_team",
        description=(
            "Send a plain-text email to every configured team member. "
            "Recipients are fixed by the server and cannot be supplied or changed."
        ),
    )
    def send_to_team(subject: str, body: str) -> dict:
        return send_mail(subject, body, settings)

    @server.tool(
        name="read_bot_mail",
        description="Read inbox messages sent by configured team members only.",
    )
    def read_bot_mail(
        limit: int = 20,
        unread_only: bool = True,
        since: str | None = None,
        mark_read: bool = False,
    ) -> dict:
        return read_mail(
            settings,
            limit=limit,
            unread_only=unread_only,
            since=since,
            mark_read=mark_read,
        )

    return server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the agent-team-mail MCP server")
    parser.add_argument(
        "--transport",
        choices=("http", "stdio"),
        default="http",
        help="MCP transport to use (default: http)",
    )
    parser.add_argument("--env-file", help="Path to a dotenv configuration file")
    return parser


def _allowed_hosts(settings: Settings) -> list[str]:
    if settings.allowed_hosts:
        return list(settings.allowed_hosts)
    return ["127.0.0.1:*", "localhost:*", "[::1]:*"]


def main(argv: Sequence[str] | None = None) -> None:
    """Load configuration and run the selected transport."""
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        settings = Settings.from_env(args.env_file)
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    server = create_server(settings)
    if args.transport == "stdio":
        server.run(transport="stdio")
        return

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts(settings),
    )
    server.run(
        transport="streamable-http",
        host=settings.bind_host,
        port=settings.port,
        streamable_http_path="/mcp",
        transport_security=security,
    )


if __name__ == "__main__":
    main()
