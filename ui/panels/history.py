"""
ui/panels/history.py
Combined history view — purchases, sales, usage, waste in one place.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTabWidget, QTableWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor

import db.database as db
from ui.widgets  import (
    make_table, table_item, centered_item, page_header,
    search_bar, hdivider, muted, stat_card
)
from ui.styles   import DANGER, WARNING, SUCCESS, ACCENT, INFO, TEXT_SECOND


class HistoryPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        root.addWidget(page_header(
            "📋  History",
            "Full activity log for purchases, sales, and waste"
        ))
        root.addWidget(hdivider())

        # Period filter (shared across tabs)
        row = QHBoxLayout()
        row.addWidget(QLabel("Period:"))
        self._period = QComboBox()
        self._period.addItems(["Last 7 days","Last 30 days",
                               "Last 90 days","All Time"])
        self._period.setCurrentIndex(1)
        self._period.currentIndexChanged.connect(self.refresh)
        self._period.setFixedWidth(140)
        row.addWidget(self._period)
        row.addStretch()
        root.addLayout(row)

        # Tabs
        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        # Purchases tab
        self._purch_tbl = make_table(
            ["Date","Item","Qty","Unit","Unit Cost","Total","Invoice","Supplier"])
        self._tabs.addTab(self._purch_tbl, "🛒  Purchases")

        # Sales tab
        self._sales_tbl = make_table(
            ["Date","Menu Item","Category","Qty Sold","Logged By"])
        self._tabs.addTab(self._sales_tbl, "🥪  Sales")

        # Usage tab
        self._usage_tbl = make_table(
            ["Date","Item","Qty","Unit","Reason","Logged By"])
        self._tabs.addTab(self._usage_tbl, "📤  Manual Usage")

        # Waste tab
        self._waste_tbl = make_table(
            ["Date","Item","Qty","Unit","Reason","Est. Cost","Logged By"])
        self._tabs.addTab(self._waste_tbl, "🗑  Waste")

    def refresh(self):
        days_map = {0: 7, 1: 30, 2: 90, 3: 36500}
        days = days_map[self._period.currentIndex()]
        self._load_purchases(days)
        self._load_sales(days)
        self._load_usage(days)
        self._load_waste(days)

    def _load_purchases(self, days: int):
        rows = db.get_purchase_history(limit=1000)
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = [r for r in rows if r['purchased_at'] >= cutoff]
        tbl  = self._purch_tbl
        tbl.setRowCount(len(rows))
        for r, p in enumerate(rows):
            tbl.setItem(r, 0, table_item(p['purchased_at'][:16]))
            tbl.setItem(r, 1, table_item(p['item_name']))
            tbl.setItem(r, 2, centered_item(f"{p['quantity']:g}"))
            tbl.setItem(r, 3, centered_item(p['unit_abbr']))
            tbl.setItem(r, 4, centered_item(f"${p['unit_cost']:.2f}"))
            tc = centered_item(f"${(p['total_cost'] or 0):.2f}")
            tc.setForeground(QColor(ACCENT))
            tbl.setItem(r, 5, tc)
            tbl.setItem(r, 6, centered_item(p['invoice_number'] or "—"))
            tbl.setItem(r, 7, table_item(p['supplier'] or "—"))
            tbl.setRowHeight(r, 34)

    def _load_sales(self, days: int):
        rows = db.get_sales_history(days=days)
        tbl  = self._sales_tbl
        tbl.setRowCount(len(rows))
        for r, s in enumerate(rows):
            tbl.setItem(r, 0, table_item(s['sold_at'][:16]))
            tbl.setItem(r, 1, table_item(s['menu_item_name']))
            tbl.setItem(r, 2, table_item(s['category'] or "—"))
            tbl.setItem(r, 3, centered_item(str(s['quantity_sold'])))
            tbl.setItem(r, 4, table_item(s['logged_by'] or "—"))
            tbl.setRowHeight(r, 34)

    def _load_usage(self, days: int):
        rows = db.get_usage_history(days=days)
        tbl  = self._usage_tbl
        tbl.setRowCount(len(rows))
        for r, u in enumerate(rows):
            tbl.setItem(r, 0, table_item(u['used_at'][:16]))
            tbl.setItem(r, 1, table_item(u['item_name']))
            tbl.setItem(r, 2, centered_item(f"{u['quantity']:g}"))
            tbl.setItem(r, 3, centered_item(u['unit_abbr']))
            tbl.setItem(r, 4, table_item(u['reason'] or "—"))
            tbl.setItem(r, 5, table_item(u['logged_by'] or "—"))
            tbl.setRowHeight(r, 34)

    def _load_waste(self, days: int):
        rows = db.get_waste_history(days=days)
        tbl  = self._waste_tbl
        tbl.setRowCount(len(rows))
        reason_labels = {
            'expired':'Expired','spoiled':'Spoiled','dropped':'Dropped',
            'overproduction':'Over-prepared','quality_issue':'Quality Issue',
            'other':'Other'
        }
        for r, w in enumerate(rows):
            tbl.setItem(r, 0, table_item(w['wasted_at'][:16]))
            tbl.setItem(r, 1, table_item(w['item_name']))
            tbl.setItem(r, 2, centered_item(f"{w['quantity']:g}"))
            tbl.setItem(r, 3, centered_item(w['unit_abbr']))
            tbl.setItem(r, 4, table_item(
                reason_labels.get(w['reason'], w['reason'])))
            cost_str = f"${w['estimated_cost']:.2f}" if w['estimated_cost'] else "—"
            ci = centered_item(cost_str)
            if w['estimated_cost']:
                ci.setForeground(QColor(DANGER))
            tbl.setItem(r, 5, ci)
            tbl.setItem(r, 6, table_item(w['logged_by'] or "—"))
            tbl.setRowHeight(r, 34)
