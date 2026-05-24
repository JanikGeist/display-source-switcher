class MockMonitor:
    def __init__(self, index: int, name: str = "HP X27q", initial_input: int = 15):
        self._input = initial_input
        self._name = name
        self._index = index

    def __enter__(self) -> "MockMonitor":
        return self

    def __exit__(self, *args) -> bool:
        return False

    def get_input_source(self) -> int:
        return self._input

    def set_input_source(self, value) -> None:
        # Accepts both plain int and InputSource enum (or any object with .value)
        self._input = value.value if hasattr(value, "value") else int(value)

    def get_vcp_capabilities(self) -> dict:
        return {"model": self._name, "inputs": [0x0F, 0x11]}


def get_mock_monitors(n: int = 2) -> list[MockMonitor]:
    return [MockMonitor(index=i) for i in range(n)]
