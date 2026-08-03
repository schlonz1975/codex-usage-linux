# Privacy

Codex Usage for Linux is designed to run locally.

## Data it reads

The application starts the locally installed Codex CLI in app-server mode and
requests the current Codex rate-limit windows. It reads the remaining
percentage, reset time, window duration, plan label, and limit identifier
needed to render the widget.

## Data it stores

The application stores only:

- panel layout configuration managed by KDE Plasma;
- display preferences under `~/.config/codex-usage`;
- notification markers under `~/.local/state/codex-usage`.

It does not store prompts, chats, API keys, access tokens, or account
credentials.

## Network and telemetry

The application has no analytics, telemetry, crash-reporting SDK, or direct
network client. The Codex CLI may communicate with OpenAI using its existing
authenticated session when it serves a rate-limit request. The usage-page
button opens the official ChatGPT page in the default browser.

## Removal

`./scripts/uninstall.sh` removes the program, widget, icon, launchers, and
autostart entry. Notification markers remain unless removed manually; they
contain only limit-window identifiers, reset timestamps, and thresholds.
