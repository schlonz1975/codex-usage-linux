# Contributing

Thanks for helping improve Codex Usage for Linux.

## Before opening a pull request

1. Keep changes focused and avoid unrelated formatting rewrites.
2. Preserve compatibility with both `rateLimits` and
   `rateLimitsByLimitId` app-server responses.
3. Add or update tests for parser, notification, or service behavior.
4. Run `make test` and `git diff --check`.
5. Test QML changes with Plasma 6 when possible:

   ```bash
   plasmawindowed com.brkmen.codexusage
   ```

Never commit Codex credentials, `auth.json`, prompts, usage data, generated
notification state, or screenshots containing private information.

## Code layout

- `codex_usage/` — Python usage client, service, notifications, and fallback tray.
- `plasmoid/` — KDE Plasma 6 widget.
- `packaging/` — desktop and autostart templates.
- `scripts/` — installation, removal, and verification.
- `tests/` — standard-library unit tests.

By contributing, you agree that your contribution is provided under the MIT
License.
