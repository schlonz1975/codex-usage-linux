import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    readonly property string serviceName: "com.brkmen.CodexUsage"
    readonly property string servicePath: "/com/brkmen/CodexUsage"
    readonly property string serviceInterface: "com.brkmen.CodexUsage"
    property var usage: ({"windows": [], "lowest": null})
    readonly property var windows: usage.windows || []
    readonly property int remaining: usage.lowest === null || usage.lowest === undefined ? -1 : usage.lowest
    function remainingForWindow(minutes) {
        const window = windows.find(item => item.windowMinutes === minutes)
        return window ? Math.max(0, Math.min(100, window.remaining)) : 0
    }

    // org.kde.plasma.workspace.dbus's Properties element sometimes hands back
    // a scalar (Plasma::DBus::STRING/BOOL) as a wrapped {"value": ...} object
    // instead of a plain JS value, depending on whether it arrived via the
    // initial GetAll or a later update. An object is always truthy in JS
    // regardless of what it wraps, so every read of a DBus property used for
    // its content (not just presence) needs to go through this first.
    function dbusValue(value) {
        if (value !== null && typeof value === "object" && "value" in value) {
            return value.value
        }
        return value
    }
    readonly property string errorText: backend.properties ? dbusValue(backend.properties.Error) || "" : ""
    readonly property bool loading: backend.properties ? !!dbusValue(backend.properties.Loading) : false

    readonly property string statusText: errorText.length > 0
        ? i18n("Usage unavailable")
        : remaining >= 0 ? i18n("%1% remaining", remaining) : i18n("Connecting…")

    Plasmoid.title: i18n("Codex Usage")
    Plasmoid.icon: "codex-usage"
    toolTipMainText: i18n("Codex Usage")
    toolTipSubText: root.statusText
    preferredRepresentation: compactRepresentation
    activationTogglesExpanded: true

    function parseUsage() {
        const text = backend.properties ? dbusValue(backend.properties.Data) : ""
        if (!text) {
            return
        }
        try {
            usage = JSON.parse(text)
        } catch (error) {
            console.warn("Codex Usage returned invalid data:", error)
        }
    }

    function serviceCall(member) {
        const message = DBus.dbusMessage({
            "service": serviceName,
            "path": servicePath,
            "iface": serviceInterface,
            "member": member,
            "signature": "",
            "arguments": []
        })
        DBus.SessionBus.asyncCall(message)
    }

    DBus.Properties {
        id: backend
        busType: DBus.BusType.Session
        service: root.serviceName
        path: root.servicePath
        iface: root.serviceInterface
        onPropertiesChanged: root.parseUsage()
        onRefreshed: root.parseUsage()
    }

    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: backend.updateAll()
    }

    Component.onCompleted: backend.updateAll()

    compactRepresentation: Item {
        id: compact

        Layout.minimumWidth: Kirigami.Units.iconSizes.smallMedium
        Layout.preferredWidth: height
        Layout.fillHeight: true
        implicitWidth: Kirigami.Units.iconSizes.medium
        implicitHeight: Kirigami.Units.iconSizes.medium

        Canvas {
            id: rings
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height)
            height: width
            antialiasing: true
            property real fiveHourRemaining: root.remainingForWindow(300)
            property real weeklyRemaining: root.remainingForWindow(10080)
            onFiveHourRemainingChanged: requestPaint()
            onWeeklyRemainingChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                ctx.scale(width / 64, height / 64)
                ctx.lineWidth = 3.5
                ctx.lineCap = "round"
                function ring(radius, remaining, color) {
                    ctx.beginPath()
                    ctx.strokeStyle = "#2b3745"
                    ctx.arc(32, 32, radius, 0, 2 * Math.PI)
                    ctx.stroke()
                    if (remaining > 0) {
                        ctx.beginPath()
                        ctx.strokeStyle = color
                        ctx.arc(32, 32, radius, -Math.PI / 2,
                                -Math.PI / 2 + 2 * Math.PI * remaining / 100)
                        ctx.stroke()
                    }
                }
                ring(28, fiveHourRemaining, "#2eafe8")
                ring(21.5, weeklyRemaining, "#87cef2")
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.expanded = !root.expanded
        }
    }

    fullRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        Layout.minimumHeight: content.implicitHeight + Kirigami.Units.largeSpacing * 2
        Layout.preferredWidth: Kirigami.Units.gridUnit * 22
        Layout.preferredHeight: content.implicitHeight + Kirigami.Units.largeSpacing * 2

        ColumnLayout {
            id: content
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true

                Kirigami.Icon {
                    source: "codex-usage"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                }

                ColumnLayout {
                    spacing: 0
                    PlasmaComponents.Label {
                        text: i18n("Codex Usage")
                        font.weight: Font.DemiBold
                    }
                    PlasmaComponents.Label {
                        text: root.statusText
                        opacity: 0.7
                    }
                }

                Item { Layout.fillWidth: true }
                PlasmaComponents.BusyIndicator {
                    visible: root.loading
                    running: visible
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
            }

            Repeater {
                model: root.windows

                delegate: ColumnLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    PlasmaComponents.Label {
                        text: modelData.heading
                        font.weight: Font.DemiBold
                        opacity: 0.75
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        PlasmaComponents.ProgressBar {
                            from: 0
                            to: 100
                            value: modelData.remaining
                            Layout.fillWidth: true
                        }
                        PlasmaComponents.Label {
                            text: modelData.remaining + "%"
                            font.weight: Font.DemiBold
                            font.features: {"tnum": 1}
                        }
                    }

                    PlasmaComponents.Label {
                        text: modelData.reset
                        opacity: 0.7
                    }
                }
            }

            PlasmaComponents.Label {
                visible: root.windows.length === 0
                text: root.errorText.length > 0
                    ? root.errorText
                    : i18n("Waiting for usage information…")
                wrapMode: Text.Wrap
                opacity: 0.7
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Kirigami.Theme.textColor
                opacity: 0.15
            }

            RowLayout {
                Layout.fillWidth: true

                PlasmaComponents.Button {
                    icon.name: "view-refresh"
                    text: i18n("Refresh")
                    onClicked: root.serviceCall("Refresh")
                }

                PlasmaComponents.Button {
                    icon.name: "internet-web-browser"
                    text: i18n("Open Usage Page")
                    onClicked: Qt.openUrlExternally("https://chatgpt.com/codex/settings/usage")
                }
            }
        }
    }
}
