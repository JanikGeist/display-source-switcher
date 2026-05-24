from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging
import sys
import time

# DDC/CI over DisplayPort is prone to truncated I2C packets (e.g. "unpack requires
# a buffer of 8 bytes"). Retry a few times with a short pause before giving up.
_RETRIES = 3
_RETRY_DELAY = 0.1  # seconds between attempts


@dataclass
class MonitorInfo:
    index: int
    name: str
    monitor: Any  # monitorcontrol.Monitor or MockMonitor
    current_input: int | None
    available_inputs: dict[str, int]  # label -> VCP value


class MonitorManager:
    def __init__(self, config, use_mock: bool = False):
        self._config = config
        self._use_mock = use_mock

    @staticmethod
    def is_wsl() -> bool:
        try:
            return "microsoft" in Path("/proc/version").read_text().lower()
        except (FileNotFoundError, PermissionError):
            return False

    def _should_use_mock(self) -> bool:
        return self._use_mock or self._config.mock_mode or self.is_wsl()

    def detect_monitors(self) -> list[MonitorInfo]:
        if self._should_use_mock():
            if self.is_wsl():
                logging.info("WSL detected — DDC/CI unavailable, using mock backend")
            return self._detect_mock_monitors()
        try:
            return self._detect_real_monitors()
        except Exception as e:
            logging.warning("DDC/CI detection failed (%s), falling back to mock", e)
            return self._detect_mock_monitors()

    def _detect_mock_monitors(self) -> list[MonitorInfo]:
        from .mock_backend import get_mock_monitors
        result = []
        for i, m in enumerate(get_mock_monitors(2)):
            cfg = self._get_monitor_config(i)
            result.append(MonitorInfo(
                index=i,
                name=cfg.name or f"HP X27q [{i + 1}]",
                monitor=m,
                current_input=None,
                available_inputs=cfg.inputs,
            ))
        return result

    def _detect_real_monitors(self) -> list[MonitorInfo]:
        from monitorcontrol import get_monitors
        result = []
        for i, m in enumerate(get_monitors()):
            with m:
                name = self._get_monitor_name(m, i)
            cfg = self._get_monitor_config(i)
            result.append(MonitorInfo(
                index=i,
                name=cfg.name or name,
                monitor=m,
                current_input=None,
                available_inputs=cfg.inputs,
            ))
        return result

    def _get_monitor_name(self, monitor: Any, index: int) -> str:
        if sys.platform == "win32":
            try:
                desc = getattr(getattr(monitor, "_vcp", None), "description", None)
                if desc:
                    return str(desc)
            except Exception:
                pass
        try:
            caps = monitor.get_vcp_capabilities()
            model = caps.get("model") or ""
            if model:
                return str(model)
        except Exception:
            pass
        return f"Monitor {index + 1}"

    def _get_monitor_config(self, index: int):
        from .config import MonitorConfig, DEFAULT_INPUTS
        for mc in self._config.monitors:
            if mc.index == index:
                return mc
        return MonitorConfig(index=index, name="", inputs=dict(DEFAULT_INPUTS))

    def read_input(self, info: MonitorInfo) -> int:
        last_exc: Exception = RuntimeError("no attempts made")
        for attempt in range(_RETRIES):
            if attempt:
                time.sleep(_RETRY_DELAY)
            try:
                with info.monitor as m:
                    result = m.get_input_source()
                    return result.value if hasattr(result, "value") else int(result)
            except Exception as exc:
                last_exc = exc
                logging.debug("read_input attempt %d/%d: %s", attempt + 1, _RETRIES, exc)
        raise last_exc

    def set_input(self, info: MonitorInfo, vcp_value: int) -> None:
        last_exc: Exception = RuntimeError("no attempts made")
        for attempt in range(_RETRIES):
            if attempt:
                time.sleep(_RETRY_DELAY)
            try:
                with info.monitor as m:
                    try:
                        from monitorcontrol import InputSource
                        m.set_input_source(InputSource(vcp_value))
                    except (ImportError, ValueError):
                        m.set_input_source(vcp_value)
                return
            except Exception as exc:
                last_exc = exc
                logging.debug("set_input attempt %d/%d: %s", attempt + 1, _RETRIES, exc)
        raise last_exc
