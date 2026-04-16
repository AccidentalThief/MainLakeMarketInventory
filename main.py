"""
main.py
Entry point for the Deli & Ice Cream Inventory Management System.
Run:  python main.py
"""

import sys
import os

# Ensure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QStatusBar, QSizePolicy
)
from PyQt6.QtCore    import Qt, QSize, QTimer
from PyQt6.QtGui     import QFont, QIcon, QColor, QPalette

import db.database as db
from ui.styles   import (
    STYLESHEET, SIDEBAR_W, WINDOW_W, WINDOW_H,
    ACCENT, TEXT_MUTED, SIDEBAR_BG, DARK_BG, PANEL_BG, BORDER,
    TEXT_SECOND, TEXT_PRIMARY
)
from ui.panels.dashboard import DashboardPanel
from ui.panels.inventory import InventoryPanel
from ui.panels.purchases import PurchasesPanel
from ui.panels.sales     import SalesPanel
from ui.panels.waste     import WastePanel
from ui.panels.history   import HistoryPanel


# ═══════════════════════════════════════════════════════════════════════════════
#  Sidebar nav button
# ═══════════════════════════════════════════════════════════════════════════════

class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}   {label}", parent)
        self.setObjectName("NavBtn")
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Window
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    NAV_ITEMS = [
        ("🏠", "Dashboard",   0),
        ("📦", "Inventory",   1),
        ("🛒", "Purchases",   2),
        ("🥪", "Sales",       3),
        ("🗑", "Waste Log",   4),
        ("📋", "History",     5),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🥪  Deli & Ice Cream Inventory")
        self.resize(WINDOW_W, WINDOW_H)
        self.setMinimumSize(960, 640)
        self._build_ui()
        self._navigate(0)

        # Status bar clock
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Content area (stacked pages)
        self._stack = QStackedWidget()
        self._pages = [
            DashboardPanel(),
            InventoryPanel(),
            PurchasesPanel(),
            SalesPanel(),
            WastePanel(),
            HistoryPanel(),
        ]
        for page in self._pages:
            self._stack.addWidget(page)
        root.addWidget(self._stack, 1)

        # Status bar
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

        # App logo area
        logo_widget = QWidget()
        logo_widget.setFixedHeight(80)
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 16, 16, 10)
        logo_layout.setSpacing(2)

        app_name = QLabel("🥪 DeliTrack")
        app_name.setObjectName("AppName")
        logo_layout.addWidget(app_name)

        app_sub = QLabel("Inventory Manager")
        app_sub.setObjectName("AppSub")
        logo_layout.addWidget(app_sub)

        layout.addWidget(logo_widget)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Nav buttons
        self._nav_buttons = []
        for icon, label, idx in self.NAV_ITEMS:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Bottom: version info
        ver = QLabel("v1.0  |  SQLite Local")
        ver.setObjectName("Muted")
        ver.setContentsMargins(16, 0, 16, 12)
        layout.addWidget(ver)

        return sidebar

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, index: int):
        self._current_index = index
        self._stack.setCurrentIndex(index)

        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

        # Refresh panel data when switching to it
        page = self._pages[index]
        if hasattr(page, 'refresh'):
            page.refresh()

        label = self.NAV_ITEMS[index][1]
        self.statusBar().showMessage(f"  {label}", 2000)

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now().strftime("%A, %B %d  |  %I:%M %p")
        self._status_label.setText(now + "  ")


# ═══════════════════════════════════════════════════════════════════════════════
#  Bootstrap
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Initialize DB first
    db.initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Deli Inventory")
    app.setApplicationVersion("1.0")

    # High-DPI support
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Apply stylesheet
    app.setStyleSheet(STYLESHEET)

    # Force dark palette at OS level
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#1C1C1E"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#F2F2F7"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#2C2C2E"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1C1C1E"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#F2F2F7"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#2C2C2E"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#F2F2F7"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#E8956D"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
