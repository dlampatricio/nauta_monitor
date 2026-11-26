pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons as Commons
import qs.Ui as Ui
import "Snapshot.js" as Snapshot

Ui.BarWidget {
  id: root
  moduleName: "local.nauta-monitor"
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state"
  readonly property string statusPath: setting("statusPath", stateHome + "/nauta-monitor/status.json")
  property var snapshot: null
  property double now: Date.now() / 1000
  property bool opened: false
  property bool popoutSwitchClosing: false
  property bool credentialsConfigured: false
  property bool editingCredentials: false
  property bool changingCredentials: false
  property bool showingPassword: false
  property bool confirmingRemoval: false
  property bool pendingCredentialRemoval: false
  property string accountName: ""
  property string passwordInput: ""
  property string controlMessage: ""
  property bool serviceRunning: false
  property string serviceState: ""
  property string activityLog: ""
  readonly property Ui.PluginBarApi pluginBar: bar as Ui.PluginBarApi
  readonly property string freshness: Snapshot.freshness(snapshot, now)
  readonly property string hoursText: snapshot && snapshot.hours !== null
    ? Snapshot.hoursLabel(snapshot.hours, value => Commons.I18n.formatNumber(value, 0)) : "—"

  function refresh() {
    now = Date.now() / 1000
    statusFile.reload()
  }

  function open() {
    if (!bar) return
    refresh()
    serviceState = strings.t("checkingService")
    runControl(["status"], "", "nauta-monitor-credentials")
    opened = true
    logProc.running = true
  }

  function close() {
    opened = false
  }

  function closeForPopoutSwitch() {
    popoutSwitchClosing = true
    close()
    popoutSwitchClosing = false
  }

  function runControl(args, secret, executable) {
    if (controlProc.running) return
    controlProc.command = [executable || "nauta-monitor-service"].concat(args)
    controlProc.secret = secret || ""
    controlProc.running = true
  }

  function saveCredentials() {
    if (!accountName.trim() || !passwordInput) {
      controlMessage = strings.t("credentialsRequired")
      return
    }
    changingCredentials = true
    runControl(["save"], JSON.stringify({
      username: accountName,
      password: passwordInput
    }), "nauta-monitor-credentials")
  }

  Commons.Translations {
    id: strings
    directory: Qt.resolvedUrl("i18n")
  }

  Process {
    id: controlProc
    command: ["nauta-monitor-credentials", "status"]
    stdinEnabled: true
    property string secret: ""
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          const result = JSON.parse(text)
          const args = controlProc.command
          if (args[0] === "nauta-monitor-credentials" && args[1] === "status") {
            root.credentialsConfigured = result.credentials_state === "configured"
            if (root.credentialsConfigured) root.editingCredentials = false
          } else if (args[1] === "status" && args[0] === "nauta-monitor-service") {
            root.serviceRunning = result.service_state === "active"
            root.serviceState = strings.t({
              active: "serviceActive",
              inactive: "serviceInactive",
              failed: "serviceFailed",
              "not-installed": "serviceNotInstalled",
              activating: "serviceStarting",
              deactivating: "serviceStopping"
            }[result.service_state] || "serviceUnknown")
          } else {
            root.controlMessage = result.ok
              ? strings.t("operationComplete") : strings.t("operationFailed")
          }
        } catch (_) {
          root.controlMessage = strings.t("operationFailed")
        }
      }
    }
    onStarted: {
      if (secret) {
        write(secret + "\n")
        secret = ""
      }
    }
    onExited: function(exitCode) {
      const removingForCredentials = command[0] === "nauta-monitor-service"
        && command[1] === "uninstall"
        && root.pendingCredentialRemoval
      if (command[0] === "nauta-monitor-credentials" && command[1] === "save") {
        root.passwordInput = ""
        root.changingCredentials = false
        root.showingPassword = false
        if (exitCode === 0) {
          root.editingCredentials = false
          Qt.callLater(function() { root.runControl(["install"]) })
        }
      } else if (command[0] === "nauta-monitor-credentials" && command[1] === "remove" && exitCode === 0) {
        root.credentialsConfigured = false
        root.serviceRunning = false
        root.controlMessage = strings.t("credentialsRemoved")
      }
      if (command[0] === "nauta-monitor-service" && command[1] === "uninstall"
          && root.pendingCredentialRemoval && exitCode === 0) {
        root.pendingCredentialRemoval = false
        root.serviceRunning = false
        root.serviceState = strings.t("serviceNotInstalled")
        Qt.callLater(function() {
          root.runControl(["remove"], "", "nauta-monitor-credentials")
        })
      } else if (command[0] === "nauta-monitor-service" && command[1] === "uninstall"
          && root.pendingCredentialRemoval) {
        root.pendingCredentialRemoval = false
      }
      if ((command[0] === "nauta-monitor-credentials" && command[1] === "status")
          || (command[0] === "nauta-monitor-service"
            && command[1] !== "status" && !removingForCredentials)) {
        Qt.callLater(function() {
          if (root.pendingCredentialRemoval) return
          root.runControl(["status"])
          if (!logProc.running) logProc.running = true
        })
      }
    }
  }

  Process {
    id: logProc
    command: ["journalctl", "--user", "--unit", "nauta-monitor.service", "--lines", "40", "--no-pager", "--output=short-iso"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.activityLog = text.length > 12000 ? text.slice(-12000) : text
    }
  }

  FileView {
    id: statusFile
    path: root.statusPath
    printErrors: false
    onLoaded: root.snapshot = Snapshot.parse(text())
    onLoadFailed: root.snapshot = null
  }

  // Polling also catches initial creation and atomic file replacement.
  Timer {
    interval: 30000
    running: true
    repeat: true
    onTriggered: root.refresh()
  }

  Ui.BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf124" // Font Awesome location arrow (Nerd Fonts).
    tooltipText: "Nauta Hogar"
    labelText: root.vertical || root.hoursText === "—" ? ""
      : root.hoursText + (root.freshness === "fresh" ? "" : " !")
    fixedWidth: root.vertical ? -1 : Math.ceil(slotSize
      + (labelText ? labelMetrics.advanceWidth + Commons.Style.space(4) : 0))

    TextMetrics {
      id: labelMetrics
      font.family: button.fontFamily
      font.pixelSize: button.fontSize
      text: button.labelText
    }

    onPressed: function(mouseButton) {
      if (mouseButton !== Qt.LeftButton) return
      if (root.opened) root.close()
      else root.open()
    }
  }

  Ui.KeyboardPanel {
    id: panel
    bar: root.bar
    owner: root
    anchorItem: button
    open: root.opened
    focusTarget: loadedContent
    contentWidth: fittedContentWidth(Commons.Style.space(340))
    contentHeight: fittedContentHeight(loadedContentHeight, Commons.Style.space(390))

    content: Ui.PanelKeyCatcher {
      anchors.fill: parent
      implicitHeight: rows.implicitHeight
      blocked: usernameInput.activeFocus || passwordField.activeFocus
      onCloseRequested: root.close()
      onActivateRequested: root.refresh()
      onTabRequested: direction => root.pluginBar?.switchPanelFrom(root, direction)

      Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: rows.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.VerticalFlick
        interactive: contentHeight > height
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        Column {
          id: rows
          width: parent.width
          spacing: Commons.Style.space(8)

        Detail {
          title: true
          text: "Nauta Hogar"
          font.bold: true
        }
        Detail {
          text: strings.t("balance").arg(root.snapshot && root.snapshot.credit_cup !== null
            ? Commons.I18n.formatNumber(root.snapshot.credit_cup, 2) + " CUP" : "—")
        }
        Detail { text: strings.t("hours").arg(root.hoursText) }
        Detail { text: strings.t("account").arg(root.snapshot?.account_status || "—") }
        Detail {
          text: strings.t("updated").arg(root.snapshot?.last_success_at
            ? new Date(root.snapshot.last_success_at * 1000).toLocaleString(Qt.locale(Commons.I18n.formatLocale), Locale.ShortFormat)
            : "—")
        }
        Detail { text: strings.t(root.freshness) }

        Detail { text: root.serviceState }
        Detail { text: root.controlMessage; visible: root.controlMessage !== "" }

        Column {
          width: parent.width
          spacing: Commons.Style.space(6)
          visible: root.editingCredentials || !root.credentialsConfigured

          TextField {
            id: usernameInput
            width: parent.width
            placeholderText: strings.t("username")
            text: root.accountName
            font.family: Commons.Style.fontFamily
            font.pixelSize: Commons.Style.space(12)
            onTextChanged: root.accountName = text
          }
          TextField {
            id: passwordField
            width: parent.width
            placeholderText: strings.t("password")
            echoMode: root.showingPassword ? TextInput.Normal : TextInput.Password
            text: root.passwordInput
            font.family: Commons.Style.fontFamily
            font.pixelSize: Commons.Style.space(12)
            onTextChanged: root.passwordInput = text
          }
          GridLayout {
            width: parent.width
            columns: 2
            columnSpacing: Commons.Style.space(8)
            rowSpacing: Commons.Style.space(6)
            Ui.Button {
              Layout.fillWidth: true
              Layout.minimumWidth: 0
              fontSize: Commons.Style.space(12)
              text: strings.t(root.showingPassword ? "hidePassword" : "showPassword")
              onClicked: root.showingPassword = !root.showingPassword
            }
            Ui.Button {
              Layout.fillWidth: true
              Layout.minimumWidth: 0
              fontSize: Commons.Style.space(12)
              text: strings.t("saveAndStart")
              enabled: !controlProc.running && !root.changingCredentials
              onClicked: root.saveCredentials()
            }
            Ui.Button {
              Layout.fillWidth: true
              Layout.minimumWidth: 0
              fontSize: Commons.Style.space(12)
              text: strings.t("cancel")
              visible: root.credentialsConfigured
              onClicked: {
                root.editingCredentials = false
                root.passwordInput = ""
              }
            }
          }
        }

        GridLayout {
          width: parent.width
          columns: 2
          columnSpacing: Commons.Style.space(8)
          rowSpacing: Commons.Style.space(6)
          visible: root.credentialsConfigured && !root.editingCredentials
          Ui.Button {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            fontSize: Commons.Style.space(12)
            text: strings.t(root.serviceRunning ? "stop" : "start")
            enabled: !controlProc.running
            onClicked: root.runControl([root.serviceRunning ? "stop" : "start"])
          }
          Ui.Button {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            fontSize: Commons.Style.space(12)
            text: strings.t("checkNow")
            enabled: root.serviceRunning && !controlProc.running
            onClicked: root.runControl(["restart"])
          }
          Ui.Button {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            fontSize: Commons.Style.space(12)
            text: strings.t("changeCredentials")
            onClicked: {
              root.editingCredentials = true
              root.passwordInput = ""
            }
          }
          Ui.Button {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            fontSize: Commons.Style.space(12)
            text: strings.t(root.confirmingRemoval ? "confirmRemove" : "removeCredentials")
            onClicked: {
              if (root.confirmingRemoval) {
                root.confirmingRemoval = false
                root.pendingCredentialRemoval = true
                root.runControl(["uninstall"])
              } else {
                root.confirmingRemoval = true
              }
            }
          }
        }

        ScrollView {
          width: parent.width
          height: Commons.Style.space(120)
          implicitHeight: height
          clip: true
          TextArea {
            textFormat: TextEdit.PlainText
            readOnly: true
            wrapMode: TextEdit.WordWrap
            selectByMouse: true
            font.family: "monospace"
            font.pixelSize: Commons.Style.space(12)
            width: parent.width
            height: parent.height
            implicitHeight: height
            text: root.activityLog || strings.t("noActivity")
          }
        }

          Ui.Button {
            text: strings.t("refresh")
            bordered: true
            fontSize: Commons.Style.space(12)
            width: parent.width
            onClicked: {
              root.refresh()
              if (!logProc.running) logProc.running = true
            }
          }
        }
      }
    }
  }

  Timer {
    interval: 5000
    running: root.opened
    repeat: true
    onTriggered: {
      if (!controlProc.running) root.runControl(["status"])
      if (!logProc.running) logProc.running = true
    }
  }

  component Detail: Text {
    property bool title: false
    width: parent.width
    textFormat: Text.PlainText
    wrapMode: Text.Wrap
    maximumLineCount: 2
    elide: Text.ElideRight
    color: Commons.Color.foreground
    font.family: Commons.Style.fontFamily
    font.pixelSize: title ? Commons.Style.space(14) : Commons.Style.space(12)
  }
}
