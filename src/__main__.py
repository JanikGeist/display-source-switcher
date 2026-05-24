import argparse
import logging
import os
import sys


def main():
    parser = argparse.ArgumentParser(prog="ScreenSwitchWidget")
    parser.add_argument("--mock", action="store_true", help="Use mock monitors (no DDC/CI)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", metavar="PATH", help="Path to config file")
    parser.add_argument("--reset-config", action="store_true", help="Reset config to defaults")
    parser.add_argument(
        "--window", action="store_true",
        help="Show popup as a standalone window instead of system tray (for dev/WSL)",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    use_mock = args.mock or os.environ.get("SCREENSWITCHWIDGET_MOCK") == "1"

    from .config import get_default_config, load_config, save_config

    config = load_config(args.config)

    if args.reset_config:
        save_config(get_default_config(), args.config)
        print("Config reset to defaults.")
        sys.exit(0)

    if config.mock_mode:
        use_mock = True

    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

    app = QApplication(sys.argv)
    app.setApplicationName("ScreenSwitchWidget")
    app.setQuitOnLastWindowClosed(False)

    window_mode = args.window
    if not window_mode and not QSystemTrayIcon.isSystemTrayAvailable():
        if use_mock:
            logging.warning("System tray unavailable — falling back to window mode")
            window_mode = True
        else:
            QMessageBox.critical(
                None,
                "ScreenSwitchWidget",
                "System tray is not available.\n"
                "Please ensure a system tray is running (KDE, XFCE, GNOME + AppIndicator, etc.).\n\n"
                "Tip: run with --mock --window for development without a system tray.",
            )
            sys.exit(1)

    if window_mode:
        app.setQuitOnLastWindowClosed(True)

    from .app import TrayApp

    _tray_app = TrayApp(config, use_mock=use_mock, window_mode=window_mode)  # noqa: F841
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
