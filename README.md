# Codex Usage for Linux

A native KDE Plasma panel widget and portable tray indicator for monitoring
remaining ChatGPT Codex usage limits on Linux.

> [!IMPORTANT]
> This is an unofficial community project. It is not affiliated with,
> sponsored by, or endorsed by OpenAI.

## Features

- Shows remaining Codex usage and reset times directly in a Plasma panel.
- Shows remaining limits as two rounded rings: blue for 5 hours, light blue for weekly.
- Keeps the panel and tray icon free of percentage text.
- Displays each available usage window in a native Plasma popup.
- Sends one desktop warning per 20%, 10%, and 5% threshold/reset window.
- Refreshes every five minutes and reconnects through the local Codex CLI.
- Starts its local data service automatically at login.
- Includes a GTK/AppIndicator tray fallback for non-Plasma desktops.
- Stores no prompts, chats, API keys, or access tokens.

## How it works

```text
Codex CLI app-server
        │
        ▼
Local Python service
        │ D-Bus
        ▼
KDE Plasma widget
```

The application starts `codex app-server` locally and calls the documented
`account/rateLimits/read` method. Authentication remains owned by the Codex
CLI. The Plasma widget only receives display-ready usage information over the
local session bus.

## Requirements

- Linux with Python 3.10 or newer.
- The [Codex CLI](https://developers.openai.com/codex/cli/), signed in with
  ChatGPT (`codex login`).
- KDE Plasma 6 for the native widget.
- Python D-Bus, PyGObject, libnotify, GTK 3, and Ayatana AppIndicator for the
  service, notifications, and portable tray fallback.

On Fedora/Nobara, the required desktop packages are commonly available as:

```bash
sudo dnf install python3-dbus python3-gobject libnotify \
  gtk3 libayatana-appindicator-gtk3 kf6-kpackage
```

## Install

Clone the repository and run the user-level installer:

```bash
git clone https://github.com/schlonz1975/codex-usage-linux.git
cd codex-usage-linux
./scripts/install.sh
```

No `sudo` is used by the installer. It installs files under `~/.local` and
creates an autostart entry under `~/.config/autostart`.

### Add the Plasma widget

1. Right-click the KDE panel and enter edit mode.
2. Select **Add Widgets**.
3. Search for **Codex Usage**.
4. Drag the widget onto the panel.

The rings show the remaining limit clockwise from the top and shrink as usage
is consumed. Click the icon
to see remaining percentages and reset times.

### Portable tray fallback

Launch **Codex Usage Tray (Fallback)** from the application menu, or run:

```bash
codex-usage
```

## Diagnostics

Verify the CLI and authenticated usage connection without printing account
details or percentages:

```bash
codex-usage --check
```

Run the automated test suite:

```bash
make test
```

## Uninstall

```bash
./scripts/uninstall.sh
```

Notification history remains under `~/.local/state/codex-usage` by design and
contains no account or prompt data.

## Privacy and security

The application contains no analytics, telemetry, crash reporting, or direct
credential handling. See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

## Project status

The project is in an early alpha stage and is currently developed and tested
on KDE Plasma 6 running on Nobara Linux. Reports from other distributions and
desktop environments are welcome.

## Credits

This Linux implementation is derived from the MIT-licensed
[Codex Usage macOS project](https://github.com/BrkMen/CodexUsage) by BrkMen.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for icon and trademark
attribution.

## License

MIT. See [LICENSE](LICENSE).
