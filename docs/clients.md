# Connecting MCP clients

Choose one of these patterns based on where the MCP client runs. Keep credentials in environment variables or the client's secret store.

## Remote client through Cloudflare Access

Many stdio-only MCP clients can use [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) as a bridge:

```bash
npx -y mcp-remote https://team-mail.example.com/mcp \
  --transport http-only \
  --header CF-Access-Client-Id:${CF_ACCESS_CLIENT_ID} \
  --header CF-Access-Client-Secret:${CF_ACCESS_CLIENT_SECRET}
```

Set `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET` in the client process environment. Do not paste their values into a checked-in JSON file, command history, issue, or agent prompt.

A generic stdio client configuration looks like:

```json
{
  "mcpServers": {
    "team-mail": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://team-mail.example.com/mcp",
        "--transport",
        "http-only",
        "--header",
        "CF-Access-Client-Id:${CF_ACCESS_CLIENT_ID}",
        "--header",
        "CF-Access-Client-Secret:${CF_ACCESS_CLIENT_SECRET}"
      ],
      "env": {
        "CF_ACCESS_CLIENT_ID": "${CF_ACCESS_CLIENT_ID}",
        "CF_ACCESS_CLIENT_SECRET": "${CF_ACCESS_CLIENT_SECRET}"
      }
    }
  }
}
```

Environment interpolation syntax differs among clients. If yours does not interpolate values, use its documented secret mechanism rather than committing literal credentials.

## Local direct HTTP

An MCP client on the same host can connect directly:

```json
{
  "mcpServers": {
    "team-mail": {
      "url": "http://127.0.0.1:8765/mcp",
      "transport": "streamable-http"
    }
  }
}
```

No tunnel token is needed for loopback access. Do not change the URL to a public address unless an authenticated proxy protects it.

## Local stdio

The client can also launch the server itself:

```json
{
  "mcpServers": {
    "team-mail": {
      "command": "/opt/agent-team-mail/.venv/bin/agent-team-mail",
      "args": [
        "--transport",
        "stdio",
        "--env-file",
        "/etc/agent-team-mail/agent-team-mail.env"
      ]
    }
  }
}
```

Protect the environment file with operating-system permissions. The child process inherits access to the mailbox credential, while the agent sees only the MCP tools.

## Suggested agent instruction

Add a narrow instruction like this to the agent that receives the tools:

> Use `agent-team-mail` as the only way to send or read email. Send only to the configured team through `send_to_team`; never seek another mail tool or recipient path. Use `read_bot_mail` only for team replies. If either tool returns an error, stop the mail task and report the error without retrying through another service.

Prompt instructions complement, but do not replace, the server's fixed allowlist and network controls.
