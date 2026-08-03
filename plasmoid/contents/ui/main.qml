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
    readonly property string panelMode: Plasmoid.configuration.panelMode || "full"

    Plasmoid.title: i18n("Codex Usage")
    Plasmoid.icon: "codex-usage"
    toolTipMainText: i18n("Codex Usage")
    toolTipSubText: remaining >= 0 ? i18n("%1% remaining", remaining) : i18n("Connecting…")
    preferredRepresentation: compactRepresentation
    activationTogglesExpanded: true

    function parseUsage() {
        const text = backend.properties ? backend.properties.Data : ""
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

        readonly property bool horizontal: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
        readonly property bool showBar: horizontal && (root.panelMode === "full" || root.panelMode === "bar")
        readonly property bool showPercentage: horizontal && (root.panelMode === "full" || root.panelMode === "compact")

        Layout.minimumWidth: horizontal ? implicitWidth : Kirigami.Units.iconSizes.smallMedium
        Layout.preferredWidth: horizontal ? implicitWidth : Kirigami.Units.iconSizes.medium
        Layout.fillHeight: true
        implicitWidth: horizontal
            ? icon.implicitWidth
                + (showBar ? battery.implicitWidth + Kirigami.Units.smallSpacing : 0)
                + (showPercentage ? percentage.implicitWidth + Kirigami.Units.smallSpacing : 0)
                + Kirigami.Units.smallSpacing * 2
            : Kirigami.Units.iconSizes.medium
        implicitHeight: Kirigami.Units.iconSizes.medium

        RowLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing

            Kirigami.Icon {
                id: icon
                source: "codex-usage"
                Layout.preferredWidth: Math.min(compact.height * 0.72, Kirigami.Units.iconSizes.medium)
                Layout.preferredHeight: Layout.preferredWidth
            }

            Item {
                id: battery
                visible: compact.showBar
                implicitWidth: Kirigami.Units.gridUnit * 2.8
                implicitHeight: Kirigami.Units.gridUnit * 0.55
                Layout.preferredWidth: implicitWidth
                Layout.preferredHeight: implicitHeight

                Rectangle {
                    anchors.fill: parent
                    radius: height / 2
                    color: Kirigami.Theme.textColor
                    opacity: 0.22
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    width: parent.width * Math.max(0, root.remaining) / 100
                    height: parent.height
                    radius: height / 2
                    color: root.remaining <= 10
                        ? Kirigami.Theme.negativeTextColor
                        : root.remaining <= 20
                            ? Kirigami.Theme.neutralTextColor
                            : Kirigami.Theme.highlightColor
                }
            }

            PlasmaComponents.Label {
                id: percentage
                visible: compact.showPercentage
                text: root.remaining >= 0 ? root.remaining + "%" : "—"
                font.weight: Font.DemiBold
                font.features: {"tnum": 1}
                Layout.alignment: Qt.AlignVCenter
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
                        text: root.remaining >= 0 ? i18n("%1% remaining", root.remaining) : i18n("Connecting…")
                        opacity: 0.7
                    }
                }

                Item { Layout.fillWidth: true }
                PlasmaComponents.BusyIndicator {
                    visible: backend.properties ? backend.properties.Loading : false
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
                text: backend.properties && backend.properties.Error
                    ? backend.properties.Error
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

                PlasmaComponents.ComboBox {
                    id: modePicker
                    model: [
                        i18n("Icon + bar + percent"),
                        i18n("Icon + bar"),
                        i18n("Icon + percent"),
                        i18n("Icon only")
                    ]
                    currentIndex: root.panelMode === "full"
                        ? 0
                        : root.panelMode === "bar"
                            ? 1
                            : root.panelMode === "compact" ? 2 : 3
                    onActivated: Plasmoid.configuration.panelMode = ["full", "bar", "compact", "icon"][currentIndex]
                }

                Item { Layout.fillWidth: true }

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
