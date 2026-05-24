from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
import os
import sys


DEFAULT_INPUTS: dict[str, int] = {"DisplayPort": 15, "HDMI": 17}


@dataclass
class MonitorConfig:
    index: int = 0
    name: str = ""
    inputs: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_INPUTS))


@dataclass
class Config:
    mock_mode: bool = False
    monitors: list[MonitorConfig] = field(default_factory=list)


def get_config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ScreenSwitchWidget" / "config.json"


def get_default_config() -> Config:
    return Config(
        mock_mode=False,
        monitors=[
            MonitorConfig(index=0, name="", inputs=dict(DEFAULT_INPUTS)),
            MonitorConfig(index=1, name="", inputs=dict(DEFAULT_INPUTS)),
        ],
    )


def load_config(path: str | None = None) -> Config:
    config_path = Path(path) if path else get_config_path()
    if not config_path.exists():
        cfg = get_default_config()
        save_config(cfg, config_path)
        return cfg
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        monitors = [
            MonitorConfig(
                index=m.get("index", i),
                name=m.get("name", ""),
                inputs=m.get("inputs", dict(DEFAULT_INPUTS)),
            )
            for i, m in enumerate(data.get("monitors", []))
        ]
        return Config(
            mock_mode=bool(data.get("mock_mode", False)),
            monitors=monitors if monitors else get_default_config().monitors,
        )
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        logging.warning("Config file malformed, using defaults")
        return get_default_config()


def save_config(config: Config, path: str | Path | None = None) -> None:
    config_path = Path(path) if path else get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "mock_mode": config.mock_mode,
        "monitors": [
            {"index": m.index, "name": m.name, "inputs": m.inputs}
            for m in config.monitors
        ],
    }
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
