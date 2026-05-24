import pytest


@pytest.fixture
def tmp_config_path(tmp_path):
    return tmp_path / "config.json"
