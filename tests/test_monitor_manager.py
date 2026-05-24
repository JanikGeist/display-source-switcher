import pytest
from src.config import get_default_config
from src.monitor_manager import MonitorInfo, MonitorManager


@pytest.fixture
def manager():
    return MonitorManager(get_default_config(), use_mock=True)


def test_detect_returns_two_monitors(manager):
    monitors = manager.detect_monitors()
    assert len(monitors) == 2


def test_detect_returns_monitor_infos(manager):
    monitors = manager.detect_monitors()
    assert all(isinstance(m, MonitorInfo) for m in monitors)


def test_monitor_indices(manager):
    monitors = manager.detect_monitors()
    assert monitors[0].index == 0
    assert monitors[1].index == 1


def test_monitor_names_not_empty(manager):
    monitors = manager.detect_monitors()
    assert all(m.name for m in monitors)


def test_available_inputs_from_config(manager):
    monitors = manager.detect_monitors()
    for m in monitors:
        assert "DisplayPort" in m.available_inputs
        assert "HDMI" in m.available_inputs
        assert m.available_inputs["DisplayPort"] == 15
        assert m.available_inputs["HDMI"] == 17


def test_current_input_is_none_after_detect(manager):
    monitors = manager.detect_monitors()
    assert all(m.current_input is None for m in monitors)


def test_read_input_returns_int(manager):
    monitors = manager.detect_monitors()
    value = manager.read_input(monitors[0])
    assert isinstance(value, int)


def test_read_input_default_value(manager):
    monitors = manager.detect_monitors()
    value = manager.read_input(monitors[0])
    assert value == 15  # MockMonitor default is DP (15)


def test_set_and_read_input(manager):
    monitors = manager.detect_monitors()
    manager.set_input(monitors[0], 17)
    assert manager.read_input(monitors[0]) == 17


def test_set_input_dp(manager):
    monitors = manager.detect_monitors()
    manager.set_input(monitors[0], 17)  # set to HDMI first
    manager.set_input(monitors[0], 15)  # switch back to DP
    assert manager.read_input(monitors[0]) == 15


def test_monitors_have_independent_state(manager):
    monitors = manager.detect_monitors()
    manager.set_input(monitors[0], 17)
    assert manager.read_input(monitors[1]) == 15  # unaffected


def test_is_wsl_returns_bool():
    result = MonitorManager.is_wsl()
    assert isinstance(result, bool)
