from __future__ import annotations

import json
import threading
import time
import webbrowser
from typing import Any

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gi

gi.require_version("GLib", "2.0")
gi.require_version("Notify", "0.7")
from gi.repository import GLib, Notify  # noqa: E402

from .client import CodexClientError, read_usage
from .notifications import NotificationMarkers, notification_text
from .usage import display_snapshots, reset_countdown, snapshot_heading


BUS_NAME = "com.brkmen.CodexUsage"
OBJECT_PATH = "/com/brkmen/CodexUsage"
INTERFACE = "com.brkmen.CodexUsage"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


class UsageService(dbus.service.Object):
    REFRESH_SECONDS = 300

    def __init__(self, bus: dbus.SessionBus) -> None:
        self.bus_name = dbus.service.BusName(BUS_NAME, bus=bus, do_not_queue=True)
        super().__init__(self.bus_name, OBJECT_PATH)
        self.data = json.dumps({"windows": [], "lowest": None}, separators=(",", ":"))
        self.loading = False
        self.error = ""
        self.updated_at = 0
        self.markers = NotificationMarkers()
        Notify.init("Codex Usage")

    def start(self) -> None:
        self.refresh()
        GLib.timeout_add_seconds(self.REFRESH_SECONDS, self._scheduled_refresh)

    @dbus.service.method(INTERFACE, in_signature="", out_signature="")
    def Refresh(self) -> None:
        self.refresh()

    @dbus.service.method(INTERFACE, in_signature="", out_signature="")
    def OpenUsagePage(self) -> None:
        webbrowser.open("https://chatgpt.com/codex/settings/usage")

    @dbus.service.method(
        PROPERTIES_INTERFACE,
        in_signature="ss",
        out_signature="v",
    )
    def Get(self, interface_name: str, property_name: str) -> Any:
        self._check_interface(interface_name)
        properties = self._properties()
        if property_name not in properties:
            raise dbus.exceptions.DBusException(
                "Unknown property", name="org.freedesktop.DBus.Error.UnknownProperty"
            )
        return properties[property_name]

    @dbus.service.method(PROPERTIES_INTERFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name: str) -> dict[str, Any]:
        self._check_interface(interface_name)
        return self._properties()

    @dbus.service.signal(PROPERTIES_INTERFACE, signature="sa{sv}as")
    def PropertiesChanged(
        self,
        interface_name: str,
        changed_properties: dict[str, Any],
        invalidated_properties: list[str],
    ) -> None:
        pass

    def refresh(self) -> None:
        if self.loading:
            return
        self.loading = True
        self._emit_properties({"Loading": dbus.Boolean(True)})
        threading.Thread(target=self._load_usage, daemon=True).start()

    def _load_usage(self) -> None:
        try:
            snapshots = display_snapshots(read_usage())
            GLib.idle_add(self._apply_snapshots, snapshots)
        except CodexClientError as error:
            GLib.idle_add(self._apply_error, str(error))

    def _apply_snapshots(self, snapshots: list[Any]) -> bool:
        windows = [
            {
                "heading": snapshot_heading(snapshot),
                "remaining": snapshot.remaining_percent,
                "reset": (
                    reset_countdown(snapshot.resets_at)
                    if snapshot.resets_at
                    else "Reset time unavailable"
                ),
            }
            for snapshot in snapshots
        ]
        lowest = min((snapshot.remaining_percent for snapshot in snapshots), default=None)
        self.data = json.dumps(
            {"windows": windows, "lowest": lowest},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.loading = False
        self.error = "" if windows else "Usage information unavailable"
        self.updated_at = int(time.time())
        self._emit_properties(self._properties())
        for snapshot in snapshots:
            if self.markers.should_notify(snapshot):
                title, body = notification_text(snapshot)
                Notify.Notification.new(title, body, "dialog-warning").show()
        return GLib.SOURCE_REMOVE

    def _apply_error(self, message: str) -> bool:
        self.loading = False
        self.error = message
        self._emit_properties(
            {
                "Loading": dbus.Boolean(False),
                "Error": dbus.String(message),
            }
        )
        return GLib.SOURCE_REMOVE

    def _properties(self) -> dict[str, Any]:
        return {
            "Data": dbus.String(self.data),
            "Loading": dbus.Boolean(self.loading),
            "Error": dbus.String(self.error),
            "UpdatedAt": dbus.Int64(self.updated_at),
        }

    def _emit_properties(self, properties: dict[str, Any]) -> None:
        self.PropertiesChanged(INTERFACE, properties, [])

    def _scheduled_refresh(self) -> bool:
        self.refresh()
        return GLib.SOURCE_CONTINUE

    @staticmethod
    def _check_interface(interface_name: str) -> None:
        if interface_name != INTERFACE:
            raise dbus.exceptions.DBusException(
                "Unknown interface", name="org.freedesktop.DBus.Error.UnknownInterface"
            )


def run_service() -> int:
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    try:
        service = UsageService(bus)
    except dbus.exceptions.NameExistsException:
        return 0
    service.start()
    GLib.MainLoop().run()
    return 0
