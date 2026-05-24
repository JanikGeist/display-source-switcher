import logging

from PySide6.QtCore import QObject, QRunnable, Signal


class _DetectSignals(QObject):
    finished = Signal(list)
    error = Signal(str)


class DetectMonitorsWorker(QRunnable):
    def __init__(self, manager):
        super().__init__()
        self.signals = _DetectSignals()
        self._manager = manager
        self.setAutoDelete(True)

    def run(self):
        try:
            monitors = self._manager.detect_monitors()
            self.signals.finished.emit(monitors)
        except Exception as e:
            self.signals.error.emit(str(e))


class _ReadSignals(QObject):
    finished = Signal(int, int)  # monitor_index, vcp_value
    error = Signal(int, str)


class ReadInputWorker(QRunnable):
    def __init__(self, manager, info):
        super().__init__()
        self.signals = _ReadSignals()
        self._manager = manager
        self._info = info
        self.setAutoDelete(True)

    def run(self):
        try:
            vcp_value = self._manager.read_input(self._info)
            self.signals.finished.emit(self._info.index, vcp_value)
        except Exception as e:
            self.signals.error.emit(self._info.index, str(e))


class _SetSignals(QObject):
    finished = Signal(int, int)  # monitor_index, vcp_value
    error = Signal(int, str)


class SetInputWorker(QRunnable):
    def __init__(self, manager, info, vcp_value: int):
        super().__init__()
        self.signals = _SetSignals()
        self._manager = manager
        self._info = info
        self._vcp_value = vcp_value
        self.setAutoDelete(True)

    def run(self):
        try:
            self._manager.set_input(self._info, self._vcp_value)
            self.signals.finished.emit(self._info.index, self._vcp_value)
        except Exception as e:
            self.signals.error.emit(self._info.index, str(e))


class _UpdateSignals(QObject):
    update_available = Signal(str, str)  # version, html_url


class CheckUpdateWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = _UpdateSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            from .updater import check_for_update
            result = check_for_update()
            if result:
                self.signals.update_available.emit(result.version, result.url)
        except Exception as exc:
            logging.debug("Update check error: %s", exc)
