from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any


@dataclass(frozen=True)
class LimitSnapshot:
    id: str
    limit_id: str
    name: str
    used_percent: float
    window_minutes: int | None
    resets_at: datetime | None
    plan_type: str | None

    @property
    def remaining_percent(self) -> int:
        value = max(0.0, min(100.0, 100.0 - self.used_percent))
        return math.floor(value + 0.5)


def warning_threshold(remaining_percent: int) -> int | None:
    return next(
        (threshold for threshold in (5, 10, 20) if remaining_percent <= threshold),
        None,
    )


def parse_limits(result: dict[str, Any]) -> list[LimitSnapshot]:
    snapshots: list[LimitSnapshot] = []
    limits_by_id = result.get("rateLimitsByLimitId")

    if isinstance(limits_by_id, dict):
        for limit_id, value in limits_by_id.items():
            if isinstance(value, dict):
                snapshots.extend(_parse_limit(str(limit_id), value))
    elif isinstance(result.get("rateLimits"), dict):
        snapshots.extend(_parse_limit("codex", result["rateLimits"]))

    return sorted(
        snapshots,
        key=lambda snapshot: (
            snapshot.limit_id != "codex",
            snapshot.limit_id,
            snapshot.window_minutes if snapshot.window_minutes is not None else 2**31,
        ),
    )


def display_snapshots(snapshots: list[LimitSnapshot]) -> list[LimitSnapshot]:
    codex = [snapshot for snapshot in snapshots if snapshot.limit_id == "codex"]
    if codex:
        return codex[:2]
    if not snapshots:
        return []
    first_id = snapshots[0].limit_id
    return [snapshot for snapshot in snapshots if snapshot.limit_id == first_id][:2]


def plan_display_name(plan_type: str | None) -> str | None:
    normalized = (plan_type or "").strip().lower()
    names = {
        "free": "Free",
        "go": "Go",
        "plus": "Plus",
        "prolite": "Pro 5x",
        "pro": "Pro 20x",
        "team": "Business",
        "self_serve_business_usage_based": "Business",
        "business": "Business",
        "ent26": "Enterprise",
        "enterprise_cbp_usage_based": "Enterprise",
        "enterprise": "Enterprise",
        "edu": "Edu",
    }
    return names.get(normalized)


def window_label(minutes: int | None) -> str:
    if minutes is None:
        return "Limit"
    if minutes == 10_080:
        return "Weekly limit"
    if minutes % 1_440 == 0:
        return f"{minutes // 1_440}-day limit"
    if minutes % 60 == 0:
        return f"{minutes // 60}-hour limit"
    return f"{minutes}-minute limit"


def reset_countdown(reset_date: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now(tz=timezone.utc)
    seconds = max(0, int((reset_date - now).total_seconds()))
    if seconds == 0:
        return "Resets shortly"
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes = remainder // 60
    if days:
        return f"Resets in {days} days {hours} hours" if hours else f"Resets in {days} days"
    if hours:
        return (
            f"Resets in {hours} hours {minutes} minutes"
            if minutes
            else f"Resets in {hours} hours"
        )
    return f"Resets in {max(1, minutes)} minutes"


def snapshot_heading(snapshot: LimitSnapshot) -> str:
    plan = plan_display_name(snapshot.plan_type)
    product = f"{snapshot.name} · {plan}" if plan else snapshot.name
    return f"{product} · {window_label(snapshot.window_minutes)}"


def _parse_limit(limit_id: str, value: dict[str, Any]) -> list[LimitSnapshot]:
    raw_name = value.get("limitName")
    name = raw_name if isinstance(raw_name, str) and raw_name else (
        "Codex" if limit_id == "codex" else limit_id
    )
    plan_type = value.get("planType")
    if not isinstance(plan_type, str):
        plan_type = None

    snapshots = []
    for window_key in ("primary", "secondary"):
        window = value.get(window_key)
        if not isinstance(window, dict):
            continue
        used_percent = window.get("usedPercent")
        if not isinstance(used_percent, (int, float)):
            continue
        window_minutes = window.get("windowDurationMins")
        if not isinstance(window_minutes, int):
            window_minutes = None
        reset_timestamp = window.get("resetsAt")
        resets_at = None
        if isinstance(reset_timestamp, (int, float)):
            resets_at = datetime.fromtimestamp(reset_timestamp, tz=timezone.utc)
        snapshots.append(
            LimitSnapshot(
                id=f"{limit_id}.{window_key}",
                limit_id=limit_id,
                name=name,
                used_percent=float(used_percent),
                window_minutes=window_minutes,
                resets_at=resets_at,
                plan_type=plan_type,
            )
        )
    return snapshots
