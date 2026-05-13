"""
main.py  –  Simplified Deli Inventory
Run:  python main.py
Three screens only: Inventory, Orders, Stock Count.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QStatusBar, QSizePolicy
)
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QColor, QPalette

import db.database as db
from ui.styles   import (
    STYLESHEET, SIDEBAR_W, WINDOW_W, WINDOW_H,
    ACCENT, TEXT_SECOND, SIDEBAR_BG, DARK_BG, BORDER, TEXT_MUTED
)
from ui.panels.inventory  import InventoryPanel
from ui.panels.orders     import OrdersPanel
from ui.panels.stockcount import StockCountPanel
from ui.panels.admin      import AdminPanel


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}   {label}", parent)
        self.setObjectName("NavBtn")
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):

    NAV_ITEMS = [
        ("📦", "Inventory",   0),
        ("🛒", "Orders",      1),
        ("📋", "Stock Count", 2),
        ("🛡️", "Admin",       3),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🥪  Deli Inventory")
        self.resize(WINDOW_W, WINDOW_H)
        self.setMinimumSize(860, 600)
        self._build_ui()
        self._navigate(0)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        self._pages = [InventoryPanel(), OrdersPanel(), StockCountPanel(), AdminPanel()]
        for page in self._pages:
            self._stack.addWidget(page)
        root.addWidget(self._stack, 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("")
        sb.addPermanentWidget(self._status_label)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(SIDEBAR_W)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_widget = QWidget()
        logo_widget.setFixedHeight(80)
        ll = QVBoxLayout(logo_widget)
        ll.setContentsMargins(16, 16, 16, 10)
        ll.setSpacing(2)
        app_name = QLabel("🥪 DeliTrack")
        app_name.setObjectName("AppName")
        ll.addWidget(app_name)
        app_sub = QLabel("Inventory Manager")
        app_sub.setObjectName("AppSub")
        ll.addWidget(app_sub)
        layout.addWidget(logo_widget)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(sep)
        layout.addSpacing(8)

        self._nav_buttons = []
        for icon, label, idx in self.NAV_ITEMS:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        ver = QLabel("v2.0  |  SQLite Local")
        ver.setObjectName("Muted")
        ver.setContentsMargins(16, 0, 16, 12)
        layout.addWidget(ver)
        return sidebar

    def _navigate(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)
        page = self._pages[index]
        if hasattr(page, 'refresh'):
            page.refresh()
        self.statusBar().showMessage(f"  {self.NAV_ITEMS[index][1]}", 2000)

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now().strftime("%A, %B %d  |  %I:%M %p")
        self._status_label.setText(now + "  ")


def main():
    db.initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Deli Inventory")
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app.setStyleSheet(STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor("#1C1C1E"))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor("#F2F2F7"))
    palette.setColor(QPalette.ColorRole.Base,          QColor("#2C2C2E"))
    palette.setColor(QPalette.ColorRole.Text,          QColor("#F2F2F7"))
    palette.setColor(QPalette.ColorRole.Highlight,     QColor("#E8956D"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
