# Remote access with Cloudflare Tunnel and Access

The MCP server has no built-in user authentication. Never publish it directly to the internet. This guide keeps it on localhost and puts both Cloudflare Tunnel and Cloudflare Access in front of it.

Cloudflare product screens and commands can change; consult current Cloudflare documentation alongside this overview.

## 1. Run the server locally

Configure `agent-team-mail` to use its defaults:

```dotenv
BIND_HOST=127.0.0.1
PORT=8765
```

Confirm the service is listening only on loopback:

```bash
curl -i http://127.0.0.1:8765/mcp
```

An MCP endpoint may reject an ordinary `GET`; receiving an HTTP response still confirms connectivity.

## 2. Install and authenticate cloudflared

Install `cloudflared` using Cloudflare's package or binary instructions, then authenticate:

```bash
cloudflared tunnel login
cloudflared tunnel create agent-team-mail
```

Keep the generated tunnel credentials readable only by the account running `cloudflared`.

## 3. Add a public hostname route

In the Cloudflare Zero Trust dashboard, add a public hostname such as:

```text
team-mail.example.com
```

Route it to:

```text
http://localhost:8765
```

In the route's additional HTTP settings, set **HTTP Host Header** to:

```text
localhost:8765
```

This setting matters. The MCP SDK protects against DNS rebinding and rejects unexpected hostnames with `421 Invalid Host header`. Rewriting the origin Host header lets the request match the server's safe localhost allowlist. Alternatively, add the one expected hostname to `ALLOWED_HOSTS`; do not use a broad wildcard.

Route the DNS name to the tunnel and install `cloudflared` as a service using the platform-specific Cloudflare instructions.

## 4. Require Cloudflare Access

Before using the hostname:

1. Create a Cloudflare Access **Self-hosted** application for `team-mail.example.com`.
2. Add a **Service Auth** policy. Do not add a public bypass policy.
3. Create a service token for the MCP client.
4. Store the generated client ID and client secret in the client's secret manager or environment, never in source control.

The server should not be reachable until this policy is active.

## 5. Verify enforcement

Without a token, the request must be denied:

```bash
curl -i https://team-mail.example.com/mcp
```

Expect `403 Forbidden` (or an Access authentication response), not an MCP response.

With token values stored in the shell environment:

```bash
curl -i \
  -H "CF-Access-Client-Id: ${CF_ACCESS_CLIENT_ID}" \
  -H "CF-Access-Client-Secret: ${CF_ACCESS_CLIENT_SECRET}" \
  https://team-mail.example.com/mcp
```

This request should pass Access. A method- or MCP-protocol-specific response from the origin is sufficient to prove that authentication and routing work. Then configure an MCP client as shown in [clients.md](clients.md).

Rotate service tokens periodically, revoke unused tokens, and review Access logs. Never expose this MCP endpoint without Access or equivalent authentication.

## Alternatives

For environments that do not need a public hostname, a Tailscale network or a tightly controlled private LAN/reverse proxy can be simpler. Keep the service restricted to trusted peers and add authentication at the network or proxy layer.
