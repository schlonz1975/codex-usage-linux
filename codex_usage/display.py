from __future__ import annotations

import json
import os
from pathlib import Path


DISPLAY_BATTERY = "battery"
DISPLAY_PERCENTAGE = "percentage"
DISPLAY_MODES = (DISPLAY_BATTERY, DISPLAY_PERCENTAGE)


class DisplaySettings:
    def __init__(self, path: Path | None = None) -> None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = path or config_home / "codex-usage" / "settings.json"
        self.mode = self._load()

    def toggle(self) -> str:
        self.mode = (
            DISPLAY_PERCENTAGE if self.mode == DISPLAY_BATTERY else DISPLAY_BATTERY
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"display_mode": self.mode}), encoding="utf-8")
        temporary.replace(self.path)
        return self.mode

    def _load(self) -> str:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            mode = value.get("display_mode") if isinstance(value, dict) else None
            return mode if mode in DISPLAY_MODES else DISPLAY_BATTERY
        except (OSError, json.JSONDecodeError):
            return DISPLAY_BATTERY


class StatusIconRenderer:
    def __init__(self, directory: Path | None = None) -> None:
        cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        self.directory = directory or cache_home / "codex-usage" / "icons"

    def render(self, remaining: int, mode: str) -> Path:
        remaining = max(0, min(100, remaining))
        mode = mode if mode in DISPLAY_MODES else DISPLAY_BATTERY
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"status-{mode}-{remaining}.svg"
        if not path.exists():
            content = (
                self._battery_svg(remaining)
                if mode == DISPLAY_BATTERY
                else self._percentage_svg(remaining)
            )
            path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _color(remaining: int) -> str:
        if remaining <= 10:
            return "#f04b4b"
        if remaining <= 20:
            return "#f5a623"
        return "#f2f2f2"

    def _battery_svg(self, remaining: int) -> str:
        color = self._color(remaining)
        fill_width = round(36 * remaining / 100, 2)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect x="7" y="17" width="44" height="30" rx="5" fill="none" stroke="#f2f2f2" stroke-width="5"/>
  <rect x="53" y="25" width="5" height="14" rx="2" fill="#f2f2f2"/>
  <rect x="11" y="21" width="{fill_width}" height="22" rx="2" fill="{color}"/>
</svg>'''

    def _percentage_svg(self, remaining: int) -> str:
        color = self._color(remaining)
        font_size = 25 if remaining == 100 else 29
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <text x="32" y="40" text-anchor="middle" fill="{color}" font-family="sans-serif" font-size="{font_size}" font-weight="700">{remaining}%</text>
</svg>'''
