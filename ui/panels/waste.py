"""
ui/panels/waste.py
Log waste events and view waste history + cost summaries.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidgetItem, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor

import db.database as db
from ui.widgets  import (
    primary_btn, secondary_btn, make_table, table_item,
    centered_item, page_header, section_title, search_bar,
    hdivider, muted, stat_card, danger_btn
)
from ui.styles   import DANGER, WARNING, SUCCESS, ACCENT, INFO, TEXT_SECOND

WASTE_REASONS = [
    ("expired",       "Expired"),
    ("spoiled",       "Spoiled / Bad"),
    ("dropped",       "Dropped / Spilled"),
    ("overproduction","Over-prepared"),
    ("quality_issue", "Quality Issue"),
    ("other",         "Other"),
]


class WastePanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        log_btn = danger_btn("+ Log Waste")
        log_btn.clicked.connect(self._on_log_waste)

        root.addWidget(page_header(
            "🗑  Waste Log",
            "Track expired, spoiled, or discarded inventory",
            actions=[log_btn]
        ))
        root.addWidget(hdivider())

        # Stats
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(12)
        root.addLayout(self._stats_row)

        # Filter row
        row = QHBoxLayout()
        self._search = search_bar("Search waste entries…")
        self._search.textChanged.connect(self._filter)
        row.addWidget(self._search)

        row.addWidget(QLabel("Period:"))
        self._period = QComboBox()
        self._period.addItems(["Last 7 days","Last 30 days","Last 90 days"])
        self._period.setCurrentIndex(1)
        self._period.currentIndexChanged.connect(self.refresh)
        self._period.setFixedWidth(140)
        row.addWidget(self._period)

        row.addWidget(QLabel("Reason:"))
        self._reason_filter = QComboBox()
        self._reason_filter.addItem("All Reasons", None)
        for key, label in WASTE_REASONS:
            self._reason_filter.addItem(label, key)
        self._reason_filter.currentIndexChanged.connect(self._filter)
        self._reason_filter.setFixedWidth(140)
        row.addWidget(self._reason_filter)
        row.addStretch()
        root.addLayout(row)

        cols = ["Date/Time", "Item", "Qty", "Unit",
                "Reason", "Est. Cost", "Logged By", "Notes"]
        self._table = make_table(cols)
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 180)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 60)
        self._table.setColumnWidth(4, 120)
        self._table.setColumnWidth(5, 90)
        root.addWidget(self._table)

    def refresh(self):
        days_map = {0: 7, 1: 30, 2: 90}
        days = days_map[self._period.currentIndex()]
        self._waste = db.get_waste_history(days=days)
        self._rebuild_stats(days)
        self._filter()

    def _rebuild_stats(self, days: int):
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        summary = db.get_waste_summary(days)
        total_events = len(self._waste)
        total_cost   = sum(w['estimated_cost'] or 0 for w in self._waste)
        total_reason = {}
        for w in self._waste:
            total_reason[w['reason']] = total_reason.get(w['reason'], 0) + 1
        top_reason = max(total_reason, key=total_reason.get) if total_reason else "—"

        self._stats_row.addWidget(
            stat_card("Waste Events", str(total_events), WARNING))
        self._stats_row.addWidget(
            stat_card("Est. Waste Cost", f"${total_cost:,.2f}", DANGER))
        self._stats_row.addWidget(
            stat_card("Top Reason", top_reason.replace('_',' ').title(), INFO))
        self._stats_row.addStretch()

    def _filter(self):
        q      = self._search.text().lower()
        reason = self._reason_filter.currentData()
        rows   = [
            w for w in self._waste
            if (q in w['item_name'].lower() or q in (w['logged_by'] or "").lower())
            and (reason is None or w['reason'] == reason)
        ]
        self._populate_table(rows)

    def _populate_table(self, rows: list):
        tbl = self._table
        tbl.setRowCount(len(rows))
        tbl.setUpdatesEnabled(False)
        reason_labels = dict(WASTE_REASONS)
        for r, w in enumerate(rows):
            date_str = w['wasted_at'][:16].replace('T', ' ')
            tbl.setItem(r, 0, table_item(date_str))
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
            tbl.setItem(r, 7, table_item(w['notes'] or "—"))
            tbl.setRowHeight(r, 36)

            # Subtle row tint
            for c in range(tbl.columnCount()):
                existing = tbl.item(r, c)
                if existing:
                    existing.setBackground(QColor("#2A1A1A"))

        tbl.setUpdatesEnabled(True)

    def _on_log_waste(self):
        dlg = WasteDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.log_waste(**data)
                self.refresh()
                QMessageBox.information(
                    self, "Waste Logged",
                    "Waste entry recorded and inventory updated."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


# ── Waste Log Dialog ──────────────────────────────────────────────────────────

class WasteDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Waste")
        self.setMinimumWidth(420)
        self._items_data = db.get_all_items()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("⚠  Log Waste / Discarded Item")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)

        sub = muted("Quantity will be deducted from current inventory.")
        layout.addWidget(sub)
        layout.addWidget(hdivider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._item = QComboBox()
        self._item.setMinimumWidth(260)
        self._item.addItem("— Select Item —", None)
        for it in self._items_data:
            self._item.addItem(f"{it['name']} ({it['unit_abbr']})", it['id'])
        self._item.currentIndexChanged.connect(self._update_unit)
        form.addRow("Item *:", self._item)

        self._unit_lbl = QLabel("—")
        self._unit_lbl.setObjectName("Muted")
        form.addRow("Unit:", self._unit_lbl)

        self._qty = QDoubleSpinBox()
        self._qty.setDecimals(3)
        self._qty.setRange(0.001, 99999)
        self._qty.setValue(1)
        form.addRow("Quantity *:", self._qty)

        self._reason = QComboBox()
        for key, label in WASTE_REASONS:
            self._reason.addItem(label, key)
        form.addRow("Reason *:", self._reason)

        self._cost = QDoubleSpinBox()
        self._cost.setDecimals(2)
        self._cost.setRange(0, 99999)
        self._cost.setPrefix("$")
        self._cost.setToolTip("Estimated cost of the wasted goods (for COGS tracking)")
        form.addRow("Est. Cost:", self._cost)

        self._logged_by = QLineEdit()
        self._logged_by.setPlaceholderText("Your name")
        form.addRow("Logged By:", self._logged_by)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        self._notes.setPlaceholderText("Optional notes…")
        form.addRow("Notes:", self._notes)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_unit(self):
        item_id = self._item.currentData()
        if item_id:
            item = next((i for i in self._items_data if i['id'] == item_id), None)
            if item:
                self._unit_lbl.setText(
                    f"{item['unit_name']} ({item['unit_abbr']})")

    def _validate_and_accept(self):
        if not self._item.currentData():
            QMessageBox.warning(self, "Missing Info", "Please select an item.")
            return
        if not self._logged_by.text().strip():
            QMessageBox.warning(self, "Missing Info", "Please enter your name in 'Logged By'.")
            return
            
        self.accept()

    def get_data(self) -> dict:
        return {
            'item_id':        self._item.currentData(),
            'quantity':       self._qty.value(),
            'reason':         self._reason.currentData(),
            'estimated_cost': self._cost.value() or None,
            'logged_by':      self._logged_by.text().strip() or None,
            'notes':          self._notes.toPlainText().strip() or None,
        }
