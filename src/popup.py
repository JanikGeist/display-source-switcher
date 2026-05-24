from PySide6.QtCore import QEvent, Qt, Signal
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
}
QPushButton:checked {
    background: #1a6fa8;
    color: white;
    border: 1px solid #2a7fb8;
}
QPushButton:disabled {
    color: #666;
    background: #333;
}
"""


class PopupWidget(QWidget):
    input_selected = Signal(int, int)  # monitor_index, vcp_value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_STYLE)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(8)

        self._groups: dict[int, QButtonGroup] = {}
        self._persistent = False  # True in window mode — don't hide on deactivate

    def set_monitors(self, monitors) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._groups.clear()

        for info in monitors:
            self._add_row(info)

        self.adjustSize()

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
        self._layout.addWidget(row)
        self._groups[info.index] = group

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
        self.raise_()
        self.activateWindow()

    def show_as_window(self, title: str = "Screen Switch") -> None:
        """Show popup as a persistent standalone window (for development/WSL)."""
        self._persistent = True
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(title)
        self.show()

    def changeEvent(self, event) -> None:
        # Hide when another window becomes active (covers all "click outside" cases on Windows/Linux)
        if event.type() == QEvent.Type.WindowDeactivate and not self._persistent:
            self.hide()
        super().changeEvent(event)
