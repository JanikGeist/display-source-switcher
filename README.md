# ScreenSwitchWidget

A system tray widget for switching monitor input sources (HDMI ↔ DisplayPort) via DDC/CI. Click the tray icon, pick an input — no need to reach for the monitor buttons.

![Popup showing two HP X27q monitors with DisplayPort and HDMI buttons](.github/screenshot.png)

## Installation

Download the latest release from the [Releases](../../releases) page:

| Platform | File |
|---|---|
| Windows | `ScreenSwitchWidget-x.x.x-Setup.exe` |
| Linux | `ScreenSwitchWidget-x.x.x-linux.tar.gz` |

### Windows

Run the installer. It will:
- Install to `%LOCALAPPDATA%\ScreenSwitchWidget\` (no admin rights needed)
- Add a Start Menu shortcut
- Optionally start the widget automatically at login

### Linux

```bash
tar xzf ScreenSwitchWidget-x.x.x-linux.tar.gz
chmod +x ScreenSwitchWidget
./ScreenSwitchWidget
```

**Required one-time setup** — DDC/CI on Linux goes through the I2C bus, which is restricted by default:

```bash
# Load the i2c-dev kernel module (persistent across reboots)
echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf
sudo modprobe i2c-dev

# Allow your user to access I2C devices without sudo
sudo usermod -aG i2c $USER

# Log out and back in for the group change to take effect
```

To start automatically at login, add the binary to your desktop environment's autostart (GNOME: *Startup Applications*, KDE: *Autostart*), or create a systemd user service.

## Usage

- **Left-click** the tray icon to open the input switcher
- **Click outside** the popup or press the **×** to close it without switching
- **Right-click** the tray icon for Refresh and Quit

The tray icon colour indicates the current state across all monitors:

| Colour | Meaning |
|---|---|
| Blue | All monitors on DisplayPort |
| Orange | All monitors on HDMI |
| Grey | Mixed inputs or unknown |

## Configuration

On first launch a config file is created at:

- **Linux:** `~/.config/ScreenSwitchWidget/config.json`
- **Windows:** `%APPDATA%\ScreenSwitchWidget\config.json`

```json
{
  "mock_mode": false,
  "monitors": [
    {
      "index": 0,
      "name": "",
      "inputs": {
        "DisplayPort": 15,
        "HDMI": 17
      }
    },
    {
      "index": 1,
      "name": "",
      "inputs": {
        "DisplayPort": 15,
        "HDMI": 17
      }
    }
  ]
}
```

The `inputs` map is label → [VCP 0x60](https://www.ddcutil.com/vcp_feature_codes/) value. Standard values:

| Input | VCP value |
|---|---|
| DisplayPort 1 | 15 |
| DisplayPort 2 | 16 |
| HDMI 1 | 17 |
| HDMI 2 | 18 |

Some monitors use non-standard codes. If switching does nothing, check what your monitor actually reports:

```bash
# Linux
ddcutil getvcp 0x60 --display 1

# Windows (PowerShell) — requires monitorcontrol installed
python -c "
from monitorcontrol import get_monitors
for m in get_monitors():
    with m: print(m.get_vcp_capabilities())
"
```

Then update the VCP values in the config file to match.

To rename a monitor in the popup, set `"name"` to any non-empty string.

## Development

**Requirements:** Python 3.11+, a desktop environment with a system tray.

```bash
git clone https://github.com/YOUR_USERNAME/ScreenSwitchWidget
cd ScreenSwitchWidget

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Run the app with mock monitors (no real DDC/CI hardware needed):

```bash
python -m src --mock
```

Run the tests:

```bash
pytest tests/ -v
```

On WSL, `--mock` is implied automatically and the popup appears as a regular window since the system tray is unavailable.

### CLI flags

| Flag | Description |
|---|---|
| `--mock` | Use two fake HP X27q monitors instead of DDC/CI |
| `--debug` | Enable debug logging (shows DDC/CI retry attempts) |
| `--window` | Show popup as a standalone window instead of system tray |
| `--config PATH` | Use a custom config file |
| `--reset-config` | Reset config to defaults and exit |

## Building

Installers are built automatically by GitHub Actions on every version tag push. To build locally:

**Linux:**
```bash
pip install pyinstaller
pyinstaller ScreenSwitchWidget.spec
# Binary: dist/ScreenSwitchWidget
```

**Windows** (must run natively, not in WSL):
```powershell
pip install pyinstaller
pyinstaller ScreenSwitchWidget-win.spec
# Then build the installer:
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAppVersion=0.1.0 installer.iss
# Installer: Output\ScreenSwitchWidget-0.1.0-Setup.exe
```

To trigger a full CI release build, push a version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Troubleshooting

**Switching is unreliable / takes multiple clicks**
DDC/CI over DisplayPort can return malformed I2C packets. The app retries up to 3 times automatically. If it still fails consistently, try enabling DDC/CI in your monitor's OSD menu.

**"No monitors detected" on Linux**
Make sure the `i2c-dev` module is loaded and your user is in the `i2c` group (see [Linux setup](#linux) above). On NVIDIA proprietary drivers, DDC/CI over DP may require additional Xorg config — check `ddcutil detect` for details.

**Monitor shows wrong name**
Set `"name"` in the config file to override the auto-detected name.

**Windows Defender flags the exe**
PyInstaller-bundled executables are sometimes flagged by heuristic scanners. The source is fully open — you can audit and build it yourself.
