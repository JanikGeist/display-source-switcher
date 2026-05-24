from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

_STATE_COLORS: dict[str, QColor] = {
    "dp":      QColor(64, 144, 230),   # blue
    "hdmi":    QColor(230, 144, 64),   # orange
    "mixed":   QColor(160, 160, 160),  # gray
    "loading": QColor(200, 200, 200),  # light gray
}

_SIZE = 22


def make_tray_icon(state: str) -> QIcon:
    color = _STATE_COLORS.get(state, _STATE_COLORS["mixed"])
    pixmap = QPixmap(_SIZE, _SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Monitor bezel
    p.setPen(QColor(180, 180, 180))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(1, 2, 18, 12, 2, 2)

    # Neck
    p.drawLine(10, 14, 10, 16)

    # Base
    p.drawLine(6, 17, 15, 17)

    # Status dot (top-right corner, overlapping bezel)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawEllipse(14, 0, 7, 7)

    p.end()
    return QIcon(pixmap)
