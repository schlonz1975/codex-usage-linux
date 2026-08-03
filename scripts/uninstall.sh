#!/bin/bash

set -euo pipefail

install_root="${XDG_DATA_HOME:-$HOME/.local/share}"
app_dir="$install_root/codex-usage"

case "$app_dir" in
    "$HOME"/*/codex-usage) ;;
    *) echo "Refusing unsafe installation path: $app_dir" >&2; exit 1 ;;
esac

rm -f \
    "$HOME/.local/bin/codex-usage" \
    "$install_root/applications/codex-usage.desktop" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/codex-usage.desktop" \
    "$install_root/icons/hicolor/256x256/apps/codex-usage.png"
rm -rf "$app_dir"

if command -v kpackagetool6 >/dev/null && \
   kpackagetool6 --type Plasma/Applet --show com.brkmen.codexusage >/dev/null 2>&1; then
    kpackagetool6 --type Plasma/Applet --remove com.brkmen.codexusage
fi

echo "Uninstalled Codex Usage for Linux."
echo "Notification history remains in ${XDG_STATE_HOME:-$HOME/.local/state}/codex-usage."
