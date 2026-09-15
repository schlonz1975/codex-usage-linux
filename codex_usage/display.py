from __future__ import annotations

import math
import os
from pathlib import Path


class StatusIconRenderer:
    def __init__(self, directory: Path | None = None) -> None:
        cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        self.directory = directory or cache_home / "codex-usage" / "icons"

    def render(self, five_hour_remaining: float | None, weekly_remaining: float | None) -> Path:
        values = [round(max(0.0, min(100.0, value or 0)), 2)
                  for value in (five_hour_remaining, weekly_remaining)]
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"status-rings-v1-{values[0]}-{values[1]}.svg"
        if not path.exists():
            rings = []
            for radius, remaining, color in zip((28, 21.5), values, ("#2eafe8", "#87cef2")):
                rings.append(f'<circle cx="32" cy="32" r="{radius}" stroke="#2b3745"/>')
                if remaining >= 100:
                    rings.append(f'<circle cx="32" cy="32" r="{radius}" stroke="{color}"/>')
                elif remaining > 0:
                    angle = 2 * math.pi * remaining / 100 - math.pi / 2
                    x = 32 + radius * math.cos(angle)
                    y = 32 + radius * math.sin(angle)
                    rings.append(
                        f'<path d="M 32 {32 - radius} A {radius} {radius} 0 '
                        f'{int(remaining > 50)} 1 {x:.4f} {y:.4f}" stroke="{color}"/>'
                    )
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
                'viewBox="0 0 64 64"><g fill="none" stroke-width="3.5" '
                'stroke-linecap="round">' + "".join(rings) + '</g></svg>',
                encoding="utf-8",
            )
        return path
