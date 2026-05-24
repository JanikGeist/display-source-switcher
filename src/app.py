import logging

from PySide6.QtCore import QObject, QThreadPool, QTimer, Slot
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import Config
from .icons import make_tray_icon
from .monitor_manager import MonitorInfo, MonitorManager
from .popup import PopupWidget
from .workers import CheckUpdateWorker, DetectMonitorsWorker, ReadInputWorker, SetInputWorker

_DP_VALUES = {15, 16}
_HDMI_VALUES = {17, 18}


class TrayApp(QObject):
    def __init__(
        self,
        config: Config,
        use_mock: bool = False,
        window_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._monitors: list[MonitorInfo] = []
        self._manager = MonitorManager(config, use_mock=use_mock)
        self._pool = QThreadPool.globalInstance()
        self._window_mode = window_mode

        self._tray: QSystemTrayIcon | None = None
        self._update_url: str = ""

        if not window_mode:
            self._tray = QSystemTrayIcon(self)
            self._tray.setIcon(make_tray_icon("loading"))
            self._tray.setToolTip("Screen Switch — detecting monitors…")
            self._tray.activated.connect(self._on_tray_activated)
            self._tray.messageClicked.connect(self._on_message_clicked)
            menu = QMenu()
            menu.addAction("Refresh", self._refresh)
            menu.addSeparator()
            menu.addAction("Quit", QApplication.quit)
            self._tray.setContextMenu(menu)
            self._tray.show()
            QTimer.singleShot(5000, self._check_update)

        self._popup = PopupWidget()
        self._popup.input_selected.connect(self._on_input_selected)

        QTimer.singleShot(0, self._start_detection)

    def _start_detection(self) -> None:
        worker = DetectMonitorsWorker(self._manager)
        worker.signals.finished.connect(self._on_monitors_ready)
        worker.signals.error.connect(self._on_detection_error)
        self._pool.start(worker)

    @Slot(list)
    def _on_monitors_ready(self, monitors: list[MonitorInfo]) -> None:
        self._monitors = monitors
        self._popup.set_monitors(monitors)
        if self._tray:
            self._tray.setToolTip("Screen Switch")
        if self._window_mode:
            self._popup.show_as_window()
        for info in monitors:
            self._popup.set_monitor_loading(info.index)
            self._start_read(info)

    @Slot(str)
    def _on_detection_error(self, msg: str) -> None:
        logging.error("Monitor detection failed: %s", msg)
        if self._tray:
            self._tray.setIcon(make_tray_icon("mixed"))
            self._tray.setToolTip("Screen Switch — detection failed")

    def _start_read(self, info: MonitorInfo) -> None:
        worker = ReadInputWorker(self._manager, info)
        worker.signals.finished.connect(self._on_read_done)
        worker.signals.error.connect(self._on_read_error)
        self._pool.start(worker)

    @Slot(int, int)
    def _on_read_done(self, monitor_index: int, vcp_value: int) -> None:
        self._popup.set_monitor_ready(monitor_index)
        self._popup.set_input_active(monitor_index, vcp_value)
        for info in self._monitors:
            if info.index == monitor_index:
                info.current_input = vcp_value
                break
        self._update_tray_icon()

    @Slot(int, str)
    def _on_read_error(self, monitor_index: int, msg: str) -> None:
        logging.warning("Read input failed for monitor %d: %s", monitor_index, msg)
        self._popup.set_monitor_ready(monitor_index)

    @Slot(int, int)
    def _on_input_selected(self, monitor_index: int, vcp_value: int) -> None:
        info = next((m for m in self._monitors if m.index == monitor_index), None)
        if not info:
            return

        prev_value = info.current_input
        info.current_input = vcp_value
        self._update_tray_icon()
        self._popup.set_monitor_loading(monitor_index)

        worker = SetInputWorker(self._manager, info, vcp_value)
        worker.signals.finished.connect(self._on_set_done)
        worker.signals.error.connect(
            lambda idx, msg, prev=prev_value: self._on_set_error(idx, msg, prev)
        )
        self._pool.start(worker)

    @Slot(int, int)
    def _on_set_done(self, monitor_index: int, vcp_value: int) -> None:
        self._popup.set_monitor_ready(monitor_index)
        self._popup.set_input_active(monitor_index, vcp_value)

    def _on_set_error(self, monitor_index: int, msg: str, prev_value) -> None:
        logging.error("Set input failed for monitor %d: %s", monitor_index, msg)
        for info in self._monitors:
            if info.index == monitor_index:
                info.current_input = prev_value
                break
        self._popup.set_monitor_ready(monitor_index)
        if prev_value is not None:
            self._popup.set_input_active(monitor_index, prev_value)
        self._update_tray_icon()
        if self._tray:
            self._tray.showMessage(
                "Screen Switch — Error",
                f"Failed to switch monitor {monitor_index + 1}: {msg}",
                QSystemTrayIcon.MessageIcon.Critical,
                3000,
            )

    def _update_tray_icon(self) -> None:
        if not self._tray:
            return
        inputs = [m.current_input for m in self._monitors if m.current_input is not None]
        if not inputs:
            self._tray.setIcon(make_tray_icon("loading"))
            return
        if all(v in _DP_VALUES for v in inputs):
            self._tray.setIcon(make_tray_icon("dp"))
        elif all(v in _HDMI_VALUES for v in inputs):
            self._tray.setIcon(make_tray_icon("hdmi"))
        else:
            self._tray.setIcon(make_tray_icon("mixed"))

    @Slot()
    def _refresh(self) -> None:
        if not self._window_mode:
            self._popup.hide()
        if self._tray:
            self._tray.setIcon(make_tray_icon("loading"))
            self._tray.setToolTip("Screen Switch — refreshing…")
        self._start_detection()

    @Slot()
    def _check_update(self) -> None:
        worker = CheckUpdateWorker()
        worker.signals.update_available.connect(self._on_update_available)
        self._pool.start(worker)

    @Slot(str, str)
    def _on_update_available(self, version: str, url: str) -> None:
        logging.info("Update available: v%s", version)
        self._update_url = url
        if self._tray:
            self._tray.showMessage(
                "ScreenSwitchWidget update available",
                f"Version {version} is ready — click here to download.",
                QSystemTrayIcon.MessageIcon.Information,
                10000,
            )

    @Slot()
    def _on_message_clicked(self) -> None:
        if self._update_url:
            import webbrowser
            webbrowser.open(self._update_url)
            self._update_url = ""

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Qt.Popup closes itself on outside clicks, which includes clicks on the
            # tray icon. The activated signal fires right after, so guard against
            # immediately reopening the popup that was just dismissed by that click.
            if self._popup.isVisible():
                self._popup.hide()
            elif not self._popup.recently_hidden():
                for info in self._monitors:
                    self._popup.set_monitor_loading(info.index)
                    self._start_read(info)
                self._popup.show_near_tray(self._tray.geometry())
