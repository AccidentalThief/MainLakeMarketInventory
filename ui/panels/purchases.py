"""
ui/panels/purchases.py
Log incoming orders/purchases and view purchase history.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidgetItem, QDateEdit,
    QTextEdit, QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui  import QColor, QFont

import db.database as db
from ui.widgets  import (
    primary_btn, secondary_btn, make_table, table_item,
    centered_item, page_header, section_title, search_bar,
    hdivider, muted, stat_card
)
from ui.styles   import DANGER, WARNING, SUCCESS, ACCENT, INFO, TEXT_SECOND


class PurchasesPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        log_btn = primary_btn("+ Log Purchase")
        log_btn.clicked.connect(self._on_log_purchase)

        root.addWidget(page_header(
            "🛒  Purchases",
            "Log incoming orders and track costs",
            actions=[log_btn]
        ))
        root.addWidget(hdivider())

        # Filter row
        row = QHBoxLayout()
        self._search = search_bar("Search by item or supplier…")
        self._search.textChanged.connect(self._filter)
        row.addWidget(self._search)

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

        # Summary stats
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(12)
        root.addLayout(self._stats_row)

        # History table
        cols = ["Date", "Item", "Qty", "Unit", "Unit Cost",
                "Total Cost", "Invoice #", "Supplier", "Received By"]
        self._table = make_table(cols)
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 180)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 60)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 90)
        root.addWidget(self._table)

    def refresh(self):
        days_map = {0: 7, 1: 30, 2: 90, 3: 36500}
        days = days_map[self._period.currentIndex()]
        self._purchases = db.get_purchase_history(limit=500)
        # Filter by days
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        self._purchases = [p for p in self._purchases
                           if p['purchased_at'] >= cutoff]
        self._summary   = db.get_purchase_summary(days)
        self._rebuild_stats()
        self._filter()

    def _rebuild_stats(self):
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_cost  = sum(p['total_cost'] or 0 for p in self._purchases)
        total_orders = len(self._purchases)
        unique_items = len({p['item_id'] for p in self._purchases})

        self._stats_row.addWidget(
            stat_card("Total Purchases", str(total_orders), ACCENT))
        self._stats_row.addWidget(
            stat_card("Total COGS", f"${total_cost:,.2f}", INFO))
        self._stats_row.addWidget(
            stat_card("Unique Items", str(unique_items), SUCCESS))
        self._stats_row.addStretch()

    def _filter(self):
        q = self._search.text().lower()
        rows = [
            p for p in self._purchases
            if q in p['item_name'].lower()
            or q in (p['supplier'] or "").lower()
            or q in (p['invoice_number'] or "").lower()
        ]
        self._populate_table(rows)

    def _populate_table(self, rows: list):
        tbl = self._table
        tbl.setRowCount(len(rows))
        tbl.setUpdatesEnabled(False)

        for r, p in enumerate(rows):
            date_str = p['purchased_at'][:16].replace('T', ' ')
            tbl.setItem(r, 0, table_item(date_str))
            tbl.setItem(r, 1, table_item(p['item_name']))
            tbl.setItem(r, 2, centered_item(f"{p['quantity']:g}"))
            tbl.setItem(r, 3, centered_item(p['unit_abbr']))

            uc = centered_item(f"${p['unit_cost']:.2f}")
            uc.setForeground(QColor(TEXT_SECOND))
            tbl.setItem(r, 4, uc)

            tc = centered_item(f"${(p['total_cost'] or 0):.2f}")
            tc.setForeground(QColor(ACCENT))
            tbl.setItem(r, 5, tc)

            tbl.setItem(r, 6, centered_item(p['invoice_number'] or "—"))
            tbl.setItem(r, 7, table_item(p['supplier'] or "—"))
            tbl.setItem(r, 8, table_item(p['received_by'] or "—"))
            tbl.setRowHeight(r, 36)

        tbl.setUpdatesEnabled(True)

    def _on_log_purchase(self):
        dlg = PurchaseDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.log_purchase(**data)
                self.refresh()
                QMessageBox.information(
                    self, "Purchase Logged",
                    f"Successfully logged purchase of {data['quantity']:g} "
                    f"units and updated inventory."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


# ── Purchase Log Dialog ───────────────────────────────────────────────────────

class PurchaseDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Incoming Purchase")
        self.setMinimumWidth(440)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("Log Incoming Purchase")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)

        sub = muted("Logging a purchase will automatically update stock levels.")
        layout.addWidget(sub)
        layout.addWidget(hdivider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._item = QComboBox()
        self._item.setMinimumWidth(250)
        self._item.addItem("— Select Item —", None)
        self._items_data = db.get_all_items()
        for it in self._items_data:
            self._item.addItem(
                f"{it['name']}  ({it['unit_abbr']})", it['id'])
        self._item.currentIndexChanged.connect(self._on_item_changed)
        form.addRow("Item *:", self._item)

        self._unit_lbl = QLabel("—")
        self._unit_lbl.setObjectName("Muted")
        form.addRow("Unit:", self._unit_lbl)

        self._qty = QDoubleSpinBox()
        self._qty.setDecimals(3)
        self._qty.setRange(0.001, 99999)
        self._qty.setValue(1)
        form.addRow("Quantity *:", self._qty)

        self._unit_cost = QDoubleSpinBox()
        self._unit_cost.setDecimals(4)
        self._unit_cost.setRange(0, 99999)
        self._unit_cost.setPrefix("$")
        form.addRow("Unit Cost *:", self._unit_cost)

        self._invoice = QLineEdit()
        self._invoice.setPlaceholderText("Optional invoice / PO number")
        form.addRow("Invoice #:", self._invoice)

        self._supplier = QLineEdit()
        self._supplier.setPlaceholderText("Supplier name")
        form.addRow("Supplier:", self._supplier)

        self._received_by = QLineEdit()
        self._received_by.setPlaceholderText("Your name")
        form.addRow("Received By:", self._received_by)

        self._has_expiry = QCheckBox("Set expiration date")
        self._has_expiry.stateChanged.connect(self._toggle_expiry)
        form.addRow("", self._has_expiry)

        self._expiry = QDateEdit()
        self._expiry.setCalendarPopup(True)
        self._expiry.setDate(QDate.currentDate().addDays(7))
        self._expiry.setEnabled(False)
        form.addRow("Expiration Date:", self._expiry)

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

    def _on_item_changed(self):
        item_id = self._item.currentData()
        if item_id:
            item = next((i for i in self._items_data if i['id'] == item_id), None)
            if item:
                self._unit_lbl.setText(
                    f"{item['unit_name']} ({item['unit_abbr']})")
                self._supplier.setText(item['supplier'] or "")

    def _toggle_expiry(self, state):
        self._expiry.setEnabled(bool(state))

    def _validate_and_accept(self):
        if not self._item.currentData():
            QMessageBox.warning(self, "Validation", "Please select an item.")
            return
        if self._qty.value() <= 0:
            QMessageBox.warning(self, "Validation", "Quantity must be > 0.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'item_id':         self._item.currentData(),
            'quantity':        self._qty.value(),
            'unit_cost':       self._unit_cost.value(),
            'invoice_number':  self._invoice.text().strip() or None,
            'supplier':        self._supplier.text().strip() or None,
            'received_by':     self._received_by.text().strip() or None,
            'notes':           self._notes.toPlainText().strip() or None,
            'expiration_date': (self._expiry.date().toString("yyyy-MM-dd")
                               if self._has_expiry.isChecked() else None),
        }
