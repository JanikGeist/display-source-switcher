import json
from src.config import (
    Config,
    MonitorConfig,
    DEFAULT_INPUTS,
    get_default_config,
    load_config,
    save_config,
)


def test_default_config_structure():
    cfg = get_default_config()
    assert cfg.mock_mode is False
    assert len(cfg.monitors) == 2
    assert cfg.monitors[0].index == 0
    assert cfg.monitors[1].index == 1
    assert cfg.monitors[0].inputs == DEFAULT_INPUTS


def test_load_creates_file_when_missing(tmp_config_path):
    cfg = load_config(tmp_config_path)
    assert cfg.mock_mode is False
    assert len(cfg.monitors) == 2
    assert tmp_config_path.exists()


def test_save_load_roundtrip(tmp_config_path):
    original = Config(
        mock_mode=True,
        monitors=[
            MonitorConfig(index=0, name="Left", inputs={"DP": 15, "HDMI": 17}),
            MonitorConfig(index=1, name="Right", inputs={"DP": 15}),
        ],
    )
    save_config(original, tmp_config_path)
    loaded = load_config(tmp_config_path)
    assert loaded.mock_mode is True
    assert loaded.monitors[0].name == "Left"
    assert loaded.monitors[0].inputs == {"DP": 15, "HDMI": 17}
    assert loaded.monitors[1].name == "Right"


def test_load_malformed_json_returns_defaults(tmp_config_path):
    tmp_config_path.write_text("not valid json {{{{", encoding="utf-8")
    cfg = load_config(tmp_config_path)
    assert cfg.mock_mode is False
    assert len(cfg.monitors) == 2


def test_save_creates_parent_directories(tmp_path):
    deep = tmp_path / "a" / "b" / "config.json"
    save_config(get_default_config(), deep)
    assert deep.exists()
    data = json.loads(deep.read_text())
    assert "monitors" in data
    assert "mock_mode" in data


def test_empty_monitors_list_falls_back_to_defaults(tmp_config_path):
    tmp_config_path.write_text('{"mock_mode": false, "monitors": []}', encoding="utf-8")
    cfg = load_config(tmp_config_path)
    assert len(cfg.monitors) == 2
