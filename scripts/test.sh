#!/bin/bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
linux_dir="$(cd -- "$script_dir/.." && pwd)"

bash -n "$linux_dir"/scripts/*.sh
python3 -m compileall -q "$linux_dir/codex_usage" "$linux_dir/tests"
"$linux_dir/codex-usage" --self-test

grep -q '^Type=Application$' "$linux_dir/packaging/codex-usage.desktop.in"
grep -q '^Exec=__EXECUTABLE__$' "$linux_dir/packaging/codex-usage.desktop.in"
grep -q '^Exec=__EXECUTABLE__ --service$' "$linux_dir/packaging/codex-usage-service.desktop.in"
test -s "$linux_dir/assets/codex-tray.png"
test -s "$linux_dir/assets/codex-usage.png"
python3 -m json.tool "$linux_dir/plasmoid/metadata.json" >/dev/null
grep -q '"X-Plasma-API-Minimum-Version": "6.0"' "$linux_dir/plasmoid/metadata.json"
grep -q '^PlasmoidItem {' "$linux_dir/plasmoid/contents/ui/main.qml"
grep -q '"full", "bar", "compact", "icon"' "$linux_dir/plasmoid/contents/ui/main.qml"
grep -q 'gridUnit \* 2.8' "$linux_dir/plasmoid/contents/ui/main.qml"
grep -q 'Qt.openUrlExternally("https://chatgpt.com/codex/settings/usage")' "$linux_dir/plasmoid/contents/ui/main.qml"
if grep -q '^X-GNOME-Autostart-enabled' "$linux_dir/packaging/codex-usage.desktop.in"; then
    echo "Desktop-specific autostart key should not be required." >&2
    exit 1
fi

echo "Linux tests passed"
