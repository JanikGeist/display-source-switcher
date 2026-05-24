import logging
import time

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
    finished = Signal(int, int)  # monitor_index, confirmed_vcp_value
    error = Signal(int, str)


_VERIFY_ATTEMPTS = 3
_VERIFY_DELAY = 0.5  # seconds to wait after set before reading back


class SetAndVerifyWorker(QRunnable):
    """Sets a monitor input, then reads it back to confirm the switch happened.

    Many monitors accept DDC/CI set commands without error but silently ignore
    them. Retrying up to _VERIFY_ATTEMPTS times ensures the switch actually takes.
    """

    def __init__(self, manager, info, vcp_value: int):
        super().__init__()
        self.signals = _SetSignals()
        self._manager = manager
        self._info = info
        self._vcp_value = vcp_value
        self.setAutoDelete(True)

    def run(self):
        last_err = "no attempts made"
        for attempt in range(_VERIFY_ATTEMPTS):
            try:
                self._manager.set_input(self._info, self._vcp_value)
            except Exception as exc:
                last_err = str(exc)
                logging.debug("set+verify: set failed (attempt %d): %s", attempt + 1, exc)
                if attempt < _VERIFY_ATTEMPTS - 1:
                    time.sleep(0.1)
                continue

            time.sleep(_VERIFY_DELAY)

            try:
                actual = self._manager.read_input(self._info)
            except Exception as exc:
                logging.debug("set+verify: readback failed (attempt %d): %s", attempt + 1, exc)
                if attempt == _VERIFY_ATTEMPTS - 1:
                    # Can't confirm, but set succeeded — trust it
                    self.signals.finished.emit(self._info.index, self._vcp_value)
                    return
                continue

            if actual == self._vcp_value:
                self.signals.finished.emit(self._info.index, actual)
                return

            logging.debug(
                "set+verify: mismatch (attempt %d): expected %d, got %d",
                attempt + 1, self._vcp_value, actual,
            )
            last_err = f"expected {self._vcp_value}, got {actual}"

        self.signals.error.emit(
            self._info.index,
            f"Monitor did not switch after {_VERIFY_ATTEMPTS} attempts ({last_err})",
        )


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
