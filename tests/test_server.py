from __future__ import annotations

import asyncio

from agent_team_mail.config import Settings
from agent_team_mail.server import create_server


def test_tool_schema_has_no_recipient_parameter(settings: Settings) -> None:
    tools = asyncio.run(create_server(settings).list_tools())
    schemas = {tool.name: tool.input_schema for tool in tools}

    assert set(schemas) == {"send_to_team", "read_bot_mail"}
    assert set(schemas["send_to_team"]["properties"]) == {"subject", "body"}
    assert "recipient" not in str(schemas["send_to_team"]).lower()
