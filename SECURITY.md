# Security policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately through the repository host's security-advisory feature. Do not open a public issue containing exploit details, credentials, mailbox content, service-token values, or deployment hostnames.

Include the affected version, impact, reproduction steps, and any suggested mitigation. Maintainers will acknowledge the report and coordinate disclosure after a fix is available.

## Deployment expectations

`agent-team-mail` intentionally provides narrow mail capabilities, but operators remain responsible for deployment security:

- use a dedicated mailbox and provider-supported app credential;
- configure only intended people in `TEAM_ADDRESSES`;
- keep the HTTP listener on loopback whenever possible;
- put authenticated access control in front of every remote connection;
- limit environment-file permissions to the service account;
- run as an unprivileged, dedicated operating-system user;
- rotate mailbox and tunnel credentials after suspected exposure;
- keep Python, the MCP SDK, the base image, and the tunnel software updated;
- review mail-provider and access-proxy logs.

The MCP endpoint does not implement its own authentication. Network exposure without an authenticated tunnel or equivalent proxy is unsupported and unsafe.

## Data handling

Tool responses may contain email addresses and message bodies. Clients should avoid copying them into public logs. The server must never log or return `MAIL_APP_PASSWORD`, tunnel credentials, or raw authentication state.

The sender allowlist checks the parsed `From` header. It does not independently prove sender identity; that assurance depends on the mailbox provider's anti-spoofing controls and the security of the mailbox.

## Supported versions

Until a stable release policy is published, security fixes are applied to the latest release only.
