from src.mock_backend import MockMonitor, get_mock_monitors


def test_initial_input_default():
    m = MockMonitor(index=0)
    with m as mon:
        assert mon.get_input_source() == 15


def test_initial_input_custom():
    m = MockMonitor(index=0, initial_input=17)
    with m as mon:
        assert mon.get_input_source() == 17


def test_set_and_get_input():
    m = MockMonitor(index=0)
    with m as mon:
        mon.set_input_source(17)
    with m as mon:
        assert mon.get_input_source() == 17


def test_set_input_accepts_enum_like_object():
    class FakeEnum:
        value = 17

    m = MockMonitor(index=0)
    with m as mon:
        mon.set_input_source(FakeEnum())
        assert mon.get_input_source() == 17


def test_get_vcp_capabilities_model():
    m = MockMonitor(index=0, name="Test Monitor")
    with m as mon:
        caps = mon.get_vcp_capabilities()
    assert caps["model"] == "Test Monitor"


def test_get_vcp_capabilities_inputs():
    m = MockMonitor(index=0)
    with m as mon:
        caps = mon.get_vcp_capabilities()
    assert 0x0F in caps["inputs"]
    assert 0x11 in caps["inputs"]


def test_context_manager_returns_self():
    m = MockMonitor(index=0)
    with m as mon:
        assert mon is m


def test_get_mock_monitors_count():
    assert len(get_mock_monitors(1)) == 1
    assert len(get_mock_monitors(3)) == 3


def test_monitors_have_independent_state():
    monitors = get_mock_monitors(2)
    with monitors[0] as m0:
        m0.set_input_source(17)
    with monitors[1] as m1:
        assert m1.get_input_source() == 15
