import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

_STYLE = """
QFrame#frame {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 10px;
}
QLabel#title {
    color: #505050;
    font-size: 9px;
    letter-spacing: 1.5px;
}
QLabel#monitor_name {
    color: #888;
    font-size: 11px;
    font-weight: bold;
}
QLabel#loading_label {
    color: #505050;
    font-size: 11px;
}
QPushButton {
    background: #2a2a2a;
    color: #ccc;
    border: 1px solid #3a3a3a;
    border-radius: 5px;
    padding: 6px 0;
    font-size: 11px;
    min-width: 70px;
}
QPushButton:hover {
    background: #383838;
    border-color: #555;
}
QPushButton:checked {
    background: #1a6fa8;
    color: #fff;
    border: 1px solid #2485c7;
}
QPushButton#close_btn {
    background: transparent;
    color: #444;
    border: none;
    border-radius: 9px;
    font-size: 14px;
    padding: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
}
QPushButton#close_btn:hover {
    background: #c0392b;
    color: #fff;
}
QFrame#separator {
    background: #2d2d2d;
    max-height: 1px;
    min-height: 1px;
}
"""


class _FixedHeightStack(QStackedWidget):
    """QStackedWidget that keeps its height equal to the tallest page.

    Without this, switching from the loading page (short) to the buttons page
    (taller) resizes the popup mid-animation, which looks jarring.
    """

    def sizeHint(self):
        sh = super().sizeHint()
        if self.count():
            max_h = max(self.widget(i).sizeHint().height() for i in range(self.count()))
            from PySide6.QtCore import QSize
            return QSize(sh.width(), max(sh.height(), max_h))
        return sh

    def minimumSizeHint(self):
        msh = super().minimumSizeHint()
        if self.count():
            max_h = max(self.widget(i).minimumSizeHint().height() for i in range(self.count()))
            from PySide6.QtCore import QSize
            return QSize(msh.width(), max(msh.height(), max_h))
        return msh


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

        self._groups: dict[int, QButtonGroup] = {}
        self._stacks: dict[int, _FixedHeightStack] = {}
        self._hidden_at: float = 0.0

        # Outer layout provides shadow room (extra bottom margin for offset=5 shadow)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 20)
        outer.setSpacing(0)

        # Inner content frame — receives the drop shadow + dark background
        self._frame = QFrame()
        self._frame.setObjectName("frame")

        shadow = QGraphicsDropShadowEffect(self._frame)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._frame.setGraphicsEffect(shadow)

        outer.addWidget(self._frame)

        self._content = QVBoxLayout(self._frame)
        self._content.setContentsMargins(14, 10, 14, 14)
        self._content.setSpacing(10)

        # Header
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
        self._content.addLayout(header)

    # ── public API ────────────────────────────────────────────────────────────

    def recently_hidden(self, ms: int = 300) -> bool:
        """True if the popup was hidden within the last `ms` milliseconds.

        Guards against the tray icon click reopening the popup that Qt.Popup
        just dismissed from that same click.
        """
        return (time.monotonic() - self._hidden_at) * 1000 < ms

    def set_monitors(self, monitors) -> None:
        # Remove monitor rows (everything after the header at index 0)
        while self._content.count() > 1:
            item = self._content.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # clean up bare layouts if any
                pass
        self._groups.clear()
        self._stacks.clear()

        for i, info in enumerate(monitors):
            if i > 0:
                sep = QFrame()
                sep.setObjectName("separator")
                self._content.addWidget(sep)
            self._add_row(info)

        self.adjustSize()

    def set_input_active(self, monitor_index: int, vcp_value: int) -> None:
        group = self._groups.get(monitor_index)
        if group:
            btn = group.button(vcp_value)
            if btn:
                btn.setChecked(True)

    def set_monitor_loading(self, monitor_index: int) -> None:
        stack = self._stacks.get(monitor_index)
        if stack:
            stack.setCurrentIndex(0)

    def set_monitor_ready(self, monitor_index: int) -> None:
        stack = self._stacks.get(monitor_index)
        if stack:
            stack.setCurrentIndex(1)

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
        self._hidden_at = time.monotonic()
        super().hideEvent(event)

    # ── private ───────────────────────────────────────────────────────────────

    def _add_row(self, info) -> None:
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        name_label = QLabel(info.name)
        name_label.setObjectName("monitor_name")
        row_layout.addWidget(name_label)

        stack = _FixedHeightStack()

        # Page 0 — loading
        loading_page = QWidget()
        loading_layout = QHBoxLayout(loading_page)
        loading_layout.setContentsMargins(0, 4, 0, 4)
        loading_label = QLabel("Detecting…")
        loading_label.setObjectName("loading_label")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(loading_label)

        # Page 1 — input buttons
        buttons_page = QWidget()
        btn_layout = QHBoxLayout(buttons_page)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        group = QButtonGroup(buttons_page)
        group.setExclusive(True)

        for label_text, vcp_value in info.available_inputs.items():
            btn = QPushButton(label_text)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            group.addButton(btn, vcp_value)
            btn_layout.addWidget(btn)

        group.idClicked.connect(
            lambda vcp_id, idx=info.index: self.input_selected.emit(idx, vcp_id)
        )

        stack.addWidget(loading_page)   # index 0
        stack.addWidget(buttons_page)   # index 1
        stack.setCurrentIndex(0)

        row_layout.addWidget(stack)
        self._content.addWidget(row)

        self._stacks[info.index] = stack
        self._groups[info.index] = group
