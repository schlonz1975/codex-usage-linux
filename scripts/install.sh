#!/bin/bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
linux_dir="$(cd -- "$script_dir/.." && pwd)"
install_root="${XDG_DATA_HOME:-$HOME/.local/share}"
app_dir="$install_root/codex-usage"
bin_dir="$HOME/.local/bin"
applications_dir="$install_root/applications"
autostart_dir="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
icons_dir="$install_root/icons/hicolor/256x256/apps"
launcher="$bin_dir/codex-usage"

case "$app_dir" in
    "$HOME"/*/codex-usage) ;;
    *) echo "Refusing unsafe installation path: $app_dir" >&2; exit 1 ;;
esac

command -v codex >/dev/null || {
    echo "Codex CLI was not found in PATH." >&2
    exit 1
}

mkdir -p "$app_dir/assets" "$bin_dir" "$applications_dir" "$autostart_dir" "$icons_dir"
cp -R "$linux_dir/codex_usage" "$app_dir/"
install -m 0755 "$linux_dir/codex-usage" "$app_dir/codex-usage"
install -m 0644 "$linux_dir/assets/codex-tray.png" "$app_dir/assets/codex-tray.png"
ln -sfn "$app_dir/codex-usage" "$launcher"
install -m 0644 "$linux_dir/assets/codex-usage.png" "$icons_dir/codex-usage.png"

desktop_file="$(mktemp)"
service_desktop_file="$(mktemp)"
trap 'rm -f "$desktop_file" "$service_desktop_file"' EXIT
sed "s|__EXECUTABLE__|$launcher|g" \
    "$linux_dir/packaging/codex-usage.desktop.in" > "$desktop_file"
sed "s|__EXECUTABLE__|$launcher|g" \
    "$linux_dir/packaging/codex-usage-service.desktop.in" > "$service_desktop_file"
install -m 0644 "$desktop_file" "$applications_dir/codex-usage.desktop"
install -m 0644 "$service_desktop_file" "$autostart_dir/codex-usage.desktop"

if command -v kpackagetool6 >/dev/null; then
    if kpackagetool6 --type Plasma/Applet --show com.brkmen.codexusage >/dev/null 2>&1; then
        kpackagetool6 --type Plasma/Applet --upgrade "$linux_dir/plasmoid"
    else
        kpackagetool6 --type Plasma/Applet --install "$linux_dir/plasmoid"
    fi
else
    echo "Warning: kpackagetool6 was not found; the Plasma widget was not installed." >&2
fi

echo "Installed Codex Usage for Linux."
echo "The widget data service will start automatically the next time you log in."
echo "Add 'Codex Usage' to your Plasma panel through KDE's Add Widgets screen."
echo "For the portable tray fallback, run: $launcher"
