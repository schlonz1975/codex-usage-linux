# Security policy

## Supported versions

Security fixes are applied to the latest version on the default branch while
the project is in alpha.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability involving credential
exposure, command execution, or local privilege boundaries. Use GitHub's
private vulnerability reporting feature for this repository instead.

Include the affected version, Linux distribution, desktop environment,
reproduction steps, and expected impact. Do not include access tokens,
`~/.codex/auth.json`, prompts, or other private account data.

## Security model

- Codex authentication remains owned by the official Codex CLI.
- The widget receives display-ready data over the user's local session D-Bus.
- Installation is limited to user-owned paths and does not require root.
- No network listener is opened by this application.
