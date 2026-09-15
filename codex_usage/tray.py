from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
gi.require_version("Notify", "0.7")
from gi.repository import AyatanaAppIndicator3, GLib, Gtk, Notify  # noqa: E402

from .client import CodexClientError, read_usage
from .display import StatusIconRenderer
from .notifications import NotificationMarkers, notification_text
from .usage import (
    LimitSnapshot,
    display_snapshots,
    reset_countdown,
    snapshot_heading,
)


class UsageTray:
    REFRESH_SECONDS = 300

    def __init__(self) -> None:
        project_linux = Path(__file__).resolve().parent.parent
        installed_icon = project_linux / "assets" / "codex-tray.png"
        development_icon = project_linux.parent / "Resources" / "codex-dark.png"
        icon_path = installed_icon if installed_icon.is_file() else development_icon
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "codex-usage-linux",
            str(icon_path),
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_icon_full(str(icon_path), "Codex usage")
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Codex Usage")
        self.menu = Gtk.Menu()
        self.status_items: list[Gtk.MenuItem] = []
        self.refresh_item = Gtk.MenuItem(label="Refresh")
        self.refresh_item.connect("activate", lambda _item: self.refresh())
        dashboard_item = Gtk.MenuItem(label="Open Usage Page")
        dashboard_item.connect(
            "activate",
            lambda _item: webbrowser.open("https://chatgpt.com/codex/settings/usage"),
        )
        quit_item = Gtk.MenuItem(label="Quit Codex Usage")
        quit_item.connect("activate", lambda _item: Gtk.main_quit())
        self.actions = [
            Gtk.SeparatorMenuItem(),
            self.refresh_item,
            dashboard_item,
            Gtk.SeparatorMenuItem(),
            quit_item,
        ]
        self.markers = NotificationMarkers()
        self.icon_renderer = StatusIconRenderer()
        self.snapshots: list[LimitSnapshot] = []
        self.refreshing = False
        self._update_status_icon()
        Notify.init("Codex Usage")
        self._show_message("Connecting to Codex…")
        self.indicator.set_menu(self.menu)

    def run(self) -> None:
        self.refresh()
        GLib.timeout_add_seconds(self.REFRESH_SECONDS, self._scheduled_refresh)
        Gtk.main()

    def refresh(self) -> None:
        if self.refreshing:
            return
        self.refreshing = True
        self.refresh_item.set_sensitive(False)
        threading.Thread(target=self._load_usage, daemon=True).start()

    def _load_usage(self) -> None:
        try:
            snapshots = display_snapshots(read_usage())
            GLib.idle_add(self._apply_snapshots, snapshots)
        except CodexClientError as error:
            GLib.idle_add(self._show_error, str(error))

    def _apply_snapshots(self, snapshots: list[LimitSnapshot]) -> bool:
        self._finish_refresh()
        self.snapshots = snapshots
        self._update_status_icon()
        if not snapshots:
            self._show_message("Usage information unavailable")
            return GLib.SOURCE_REMOVE

        labels: list[str] = []
        for snapshot in snapshots:
            labels.append(snapshot_heading(snapshot))
            labels.append(f"{snapshot.remaining_percent}% left")
            labels.append(
                reset_countdown(snapshot.resets_at)
                if snapshot.resets_at
                else "Reset time unavailable"
            )
        self._replace_status_items(labels)
        lowest = min(snapshot.remaining_percent for snapshot in snapshots)
        self.indicator.set_title(f"Codex: {lowest}% left")

        for snapshot in snapshots:
            if self.markers.should_notify(snapshot):
                title, body = notification_text(snapshot)
                Notify.Notification.new(title, body, "dialog-warning").show()
        return GLib.SOURCE_REMOVE

    def _show_error(self, message: str) -> bool:
        self._finish_refresh()
        self._show_message(f"Unable to load usage\n{message}")
        self.indicator.set_title("Codex: usage unavailable")
        return GLib.SOURCE_REMOVE

    def _show_message(self, message: str) -> None:
        self._replace_status_items(message.splitlines())

    def _replace_status_items(self, labels: list[str]) -> None:
        for item in self.menu.get_children():
            self.menu.remove(item)
        self.status_items = []
        for label in labels:
            item = Gtk.MenuItem(label=label)
            item.set_sensitive(False)
            self.menu.append(item)
            self.status_items.append(item)
        for item in self.actions:
            self.menu.append(item)
        self.menu.show_all()

    def _finish_refresh(self) -> None:
        self.refreshing = False
        self.refresh_item.set_sensitive(True)

    def _scheduled_refresh(self) -> bool:
        self.refresh()
        return GLib.SOURCE_CONTINUE

    def _update_status_icon(self) -> None:
        used = {snapshot.window_minutes: snapshot.used_percent for snapshot in self.snapshots}
        icon = self.icon_renderer.render(used.get(300), used.get(10_080))
        self.indicator.set_icon_full(str(icon), "Codex usage: outer 5-hour, inner weekly")
        self.indicator.set_label("", "")
