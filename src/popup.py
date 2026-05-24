import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_STYLE = """
PopupWidget {
    background: #2b2b2b;
    border: 1px solid #555;
    border-radius: 6px;
}
QLabel#title {
    color: #666;
    font-size: 9px;
    letter-spacing: 1.5px;
    padding: 0 2px;
}
QLabel#monitor_name {
    color: #aaa;
    font-size: 11px;
    font-weight: bold;
    padding: 0 2px;
}
QPushButton {
    background: #3c3c3c;
    color: #ccc;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px 14px;
    font-size: 11px;
    min-width: 80px;
}
QPushButton:hover {
    background: #484848;
    border-color: #666;
}
QPushButton:checked {
    background: #1a6fa8;
    color: white;
    border: 1px solid #2a7fb8;
}
QPushButton:disabled {
    color: #555;
    background: #333;
    border-color: #444;
}
QPushButton#close_btn {
    background: transparent;
    color: #555;
    border: none;
    border-radius: 9px;
    font-size: 15px;
    font-weight: normal;
    padding: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
}
QPushButton#close_btn:hover {
    background: #c0392b;
    color: white;
}
"""


class PopupWidget(QWidget):
    input_selected = Signal(int, int)  # monitor_index, vcp_value

    def __init__(self, parent=None):
        super().__init__(parent)
        # Qt.Popup grabs the mouse at OS level and dismisses on any outside click —
        # the same mechanism Qt uses for menus. Reliable on Windows and Linux.
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_STYLE)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 8, 10, 10)
        self._main_layout.setSpacing(8)

        self._groups: dict[int, QButtonGroup] = {}
        self._hidden_at: float = 0.0

        # Header row: label on left, close button on right
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(0)

        title = QLabel("SCREEN SWITCH")
        title.setObjectName("title")

        close_btn = QPushButton("×")
        close_btn.setObjectName("close_btn")
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.hide)

        header.addWidget(title, stretch=1)
        header.addWidget(close_btn)
        self._main_layout.addLayout(header)

    # ── public API ────────────────────────────────────────────────────────────

    def recently_hidden(self, ms: int = 300) -> bool:
        """True if the popup was hidden within the last `ms` milliseconds.

        Used to debounce tray-icon clicks: when Qt.Popup closes on a tray click,
        the tray's activated signal fires next — without this guard it would
        immediately reopen the popup.
        """
        return (time.monotonic() - self._hidden_at) * 1000 < ms

    def set_monitors(self, monitors) -> None:
        # Remove monitor rows but keep the header layout at index 0
        while self._main_layout.count() > 1:
            item = self._main_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self._groups.clear()

        for info in monitors:
            self._add_row(info)

        self.adjustSize()

    def set_input_active(self, monitor_index: int, vcp_value: int) -> None:
        group = self._groups.get(monitor_index)
        if group:
            btn = group.button(vcp_value)
            if btn:
                btn.setChecked(True)

    def set_monitor_loading(self, monitor_index: int) -> None:
        group = self._groups.get(monitor_index)
        if group:
            for btn in group.buttons():
                btn.setEnabled(False)

    def set_monitor_ready(self, monitor_index: int) -> None:
        group = self._groups.get(monitor_index)
        if group:
            for btn in group.buttons():
                btn.setEnabled(True)

    def show_near_tray(self, tray_geom) -> None:
        self.adjustSize()
        sz = self.sizeHint()
        screen = QApplication.primaryScreen().availableGeometry()

        if not tray_geom.isNull():
            x = tray_geom.center().x() - sz.width() // 2
            y = tray_geom.top() - sz.height() - 4
        else:
            cursor = QCursor.pos()
            x = cursor.x() - sz.width() // 2
            y = cursor.y() - sz.height() - 10

        x = max(screen.left(), min(x, screen.right() - sz.width()))
        y = max(screen.top(), min(y, screen.bottom() - sz.height()))

        self.move(x, y)
        self.show()

    def show_as_window(self, title: str = "Screen Switch") -> None:
        """Persistent standalone window for development/WSL — no auto-close."""
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(title)
        self.show()

    # ── overrides ─────────────────────────────────────────────────────────────

    def hideEvent(self, event) -> None:
        # Record when we were hidden so recently_hidden() can debounce tray clicks
        self._hidden_at = time.monotonic()
        super().hideEvent(event)

    # ── private ───────────────────────────────────────────────────────────────

    def _add_row(self, info) -> None:
        row = QFrame()
        row.setStyleSheet("QFrame { background: transparent; }")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        name_label = QLabel(info.name)
        name_label.setObjectName("monitor_name")
        row_layout.addWidget(name_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        group = QButtonGroup(row)
        group.setExclusive(True)

        for label_text, vcp_value in info.available_inputs.items():
            btn = QPushButton(label_text)
            btn.setCheckable(True)
            group.addButton(btn, vcp_value)
            btn_layout.addWidget(btn)

        group.idClicked.connect(
            lambda vcp_id, idx=info.index: self.input_selected.emit(idx, vcp_id)
        )
        row_layout.addLayout(btn_layout)
        self._main_layout.addWidget(row)
        self._groups[info.index] = group
