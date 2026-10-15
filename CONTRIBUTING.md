# Contributing

Contributions are welcome. Keep changes small, documented, and consistent with the project's least-authority design.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest
```

Use Python 3.11 or newer. Add tests for behavior changes and update user documentation when configuration or tool contracts change.

## Security invariants

Changes must preserve these properties:

- `send_to_team` never accepts recipients from a caller;
- outbound recipients come only from validated `TEAM_ADDRESSES`;
- inbox results include only messages whose parsed sender is allowlisted;
- disallowed messages are not marked read;
- successful SMTP delivery is not reported as failed solely because IMAP archival failed;
- secrets are not logged, returned, committed, or included in fixtures;
- remote-access documentation requires authentication.

Do not add general mailbox search, attachment download, arbitrary headers, arbitrary folders, CC/BCC, or forwarding without a separate security discussion.

## Pull requests

Before opening a pull request:

1. Run `ruff check .` and `pytest`.
2. Check the diff for credentials, private hostnames, personal addresses, and copied production data.
3. Explain the user-visible change and its security impact.
4. Keep generated files and local environment files out of the commit.

By contributing, you agree that your contribution is licensed under the MIT License.
