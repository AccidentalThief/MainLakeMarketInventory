"""
ui/panels/dashboard.py
Home dashboard — stats at a glance, low stock alerts, expiring items.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QGridLayout, QTableWidgetItem
)
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QFont, QColor

import db.database as db
from ui.widgets  import (
    stat_card, make_table, centered_item, table_item,
    page_header, section_title, hdivider, muted, status_badge
)
from ui.styles   import (
    DANGER, WARNING, SUCCESS, ACCENT, INFO, TEXT_SECOND,
    TEXT_MUTED, PANEL_BG, BORDER
)
from datetime import date


class DashboardPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

        # Auto-refresh every 60 s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # Header
        root.addWidget(page_header(
            "🏠  Dashboard",
            "Overview of your inventory health"
        ))
        root.addWidget(hdivider())

        # Stats row
        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(12)
        root.addLayout(self._stats_grid)

        # Bottom split: low stock | expiring
        split = QHBoxLayout()
        split.setSpacing(16)

        # Low stock card
        self._low_stock_card = self._make_alert_card(
            "⚠️  Low Stock Items",
            ["Item", "Category", "Stock", "Threshold", "Unit"]
        )
        split.addWidget(self._low_stock_card['frame'], 1)

        # Expiring card
        self._expiring_card = self._make_alert_card(
            "🕒  Expiring Within 7 Days",
            ["Item", "Qty", "Unit", "Expires"]
        )
        split.addWidget(self._expiring_card['frame'], 1)

        root.addLayout(split)
        root.addStretch()

    def _make_alert_card(self, title: str, columns: list) -> dict:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        lbl = section_title(title)
        layout.addWidget(lbl)

        tbl = make_table(columns)
        tbl.setMinimumHeight(200)
        layout.addWidget(tbl)

        return {'frame': frame, 'table': tbl}

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        stats = db.get_dashboard_stats()
        self._rebuild_stats(stats)
        self._rebuild_low_stock()
        self._rebuild_expiring()

    def _rebuild_stats(self, stats: dict):
        # Clear existing
        while self._stats_grid.count():
            item = self._stats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cards = [
            stat_card("Total Items",    str(stats['total_items']),   ACCENT),
            stat_card("Low Stock",      str(stats['low_stock_count']),
                      DANGER if stats['low_stock_count'] else SUCCESS),
            stat_card("Expiring Soon",  str(stats['expiring_soon']),
                      WARNING if stats['expiring_soon'] else SUCCESS),
            stat_card("COGS (30 days)", f"${stats['cogs_30d']:,.2f}",  INFO),
            stat_card("Waste (30 days)",f"${stats['waste_cost_30d']:,.2f}", WARNING),
            stat_card("Sales Today",    str(stats['sales_today']),   SUCCESS),
        ]
        for i, card in enumerate(cards):
            self._stats_grid.addWidget(card, 0, i)

    def _rebuild_low_stock(self):
        tbl   = self._low_stock_card['table']
        items = db.get_low_stock_items()
        tbl.setRowCount(len(items))

        for r, item in enumerate(items):
            tbl.setItem(r, 0, table_item(item['name']))
            tbl.setItem(r, 1, table_item(item['category_name'] or "—"))

            qty_item = QTableWidgetItem(f"{item['current_quantity']:g}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            if item['current_quantity'] == 0:
                qty_item.setForeground(QColor(DANGER))
                qty_item.setText("OUT OF STOCK")
            else:
                qty_item.setForeground(QColor(WARNING))
            tbl.setItem(r, 2, qty_item)
            tbl.setItem(r, 3, centered_item(f"{item['min_threshold']:g}"))
            tbl.setItem(r, 4, centered_item(item['unit_abbr']))

            # Row highlight
            for c in range(tbl.columnCount()):
                existing = tbl.item(r, c)
                if existing:
                    existing.setBackground(QColor("#3A1E1E"))

        if not items:
            tbl.setRowCount(1)
            ok = QTableWidgetItem("✅  All items are well stocked")
            ok.setForeground(QColor(SUCCESS))
            ok.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(0, 0, ok)
            tbl.setSpan(0, 0, 1, 5)

    def _rebuild_expiring(self):
        tbl   = self._expiring_card['table']
        items = db.get_expiring_soon(7)
        tbl.setRowCount(len(items))
        today = date.today().isoformat()

        for r, lot in enumerate(items):
            tbl.setItem(r, 0, table_item(lot['item_name']))
            tbl.setItem(r, 1, centered_item(f"{lot['quantity']:g}"))
            tbl.setItem(r, 2, centered_item(lot['unit_abbr']))

            exp  = lot['expiration_date'] or "—"
            eitem = centered_item(exp)
            if exp <= today:
                eitem.setForeground(QColor(DANGER))
                eitem.setText(f"⚠ {exp} EXPIRED")
            else:
                eitem.setForeground(QColor(WARNING))
            tbl.setItem(r, 3, eitem)

            # Row highlight
            for c in range(tbl.columnCount()):
                existing = tbl.item(r, c)
                if existing:
                    bg = "#3A1E1E" if exp <= today else "#3A2E10"
                    existing.setBackground(QColor(bg))

        if not items:
            tbl.setRowCount(1)
            ok = QTableWidgetItem("✅  No items expiring within 7 days")
            ok.setForeground(QColor(SUCCESS))
            ok.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(0, 0, ok)
            tbl.setSpan(0, 0, 1, 4)
