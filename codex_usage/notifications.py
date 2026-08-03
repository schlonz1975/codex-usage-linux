from __future__ import annotations

import json
import os
from pathlib import Path

from .usage import LimitSnapshot, reset_countdown, warning_threshold, window_label


class NotificationMarkers:
    def __init__(self, path: Path | None = None) -> None:
        state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        self.path = path or state_home / "codex-usage" / "notifications.json"
        self._markers = self._load()

    def should_notify(self, snapshot: LimitSnapshot) -> bool:
        threshold = warning_threshold(snapshot.remaining_percent)
        if threshold is None or snapshot.resets_at is None or snapshot.limit_id != "codex":
            return False
        key = self._key(snapshot, threshold)
        if key in self._markers:
            return False
        for reached in (5, 10, 20):
            if reached >= threshold:
                self._markers.add(self._key(snapshot, reached))
        self._save()
        return True

    def _key(self, snapshot: LimitSnapshot, threshold: int) -> str:
        reset = int(snapshot.resets_at.timestamp()) if snapshot.resets_at else 0
        return f"{snapshot.id}.{reset}.{threshold}"

    def _load(self) -> set[str]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return set(value) if isinstance(value, list) else set()
        except (OSError, json.JSONDecodeError):
            return set()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(sorted(self._markers)), encoding="utf-8")
        temporary.replace(self.path)


def notification_text(snapshot: LimitSnapshot) -> tuple[str, str]:
    title = f"{window_label(snapshot.window_minutes)}: {snapshot.remaining_percent}% left"
    body = reset_countdown(snapshot.resets_at) if snapshot.resets_at else "Reset time unavailable"
    return title, body
