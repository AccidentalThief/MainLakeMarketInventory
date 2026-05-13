"""
ui/panels/orders.py  –  Simplified
Log incoming orders and view order history.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor

import db.database as db
from ui.widgets import (
    primary_btn, icon_btn, make_table, table_item, centered_item,
    page_header, search_bar, hdivider, muted, stat_card
)
from ui.styles import ACCENT, INFO, SUCCESS, TEXT_SECOND


class OrdersPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_orders = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        add_btn = primary_btn("+ Log Order")
        add_btn.clicked.connect(self._on_log)

        root.addWidget(page_header(
            "🛒  Orders",
            "Log incoming stock orders — stock levels update automatically",
            actions=[add_btn]
        ))
        root.addWidget(hdivider())

        # Stats row
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(12)
        root.addLayout(self._stats_row)

        # Filter row
        row = QHBoxLayout()
        self._search = search_bar("Search by item or supplier…")
        self._search.textChanged.connect(self._filter)
        row.addWidget(self._search)

        row.addWidget(QLabel("Period:"))
        self._period = QComboBox()
        self._period.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "All Time"])
        self._period.setCurrentIndex(1)
        self._period.currentIndexChanged.connect(self.refresh)
        self._period.setFixedWidth(140)
        row.addWidget(self._period)
        row.addStretch()
        root.addLayout(row)

        # Table
        self._table = make_table(
            ["Date", "Item", "Qty", "Unit", "Unit Cost", "Total", "Invoice #", "Supplier", "Received By"]
        )
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 180)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 60)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 90)
        root.addWidget(self._table)

    def refresh(self):
        from datetime import datetime, timedelta
        days_map = {0: 7, 1: 30, 2: 90, 3: 36500}
        days = days_map[self._period.currentIndex()]
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        all_orders = db.get_purchase_history(limit=1000)
        self._all_orders = [o for o in all_orders if o['purchased_at'] >= cutoff]
        self._rebuild_stats()
        self._filter()

    def _rebuild_stats(self):
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_cost   = sum((o['quantity'] * o['unit_cost']) for o in self._all_orders)
        total_orders = len(self._all_orders)
        unique_items = len({o['item_id'] for o in self._all_orders})

        self._stats_row.addWidget(stat_card("Orders Logged", str(total_orders), ACCENT))
        self._stats_row.addWidget(stat_card("Total Cost", f"${total_cost:,.2f}", INFO))
        self._stats_row.addWidget(stat_card("Unique Items", str(unique_items), SUCCESS))
        self._stats_row.addStretch()

    def _filter(self):
        q = self._search.text().lower()
        rows = [
            o for o in self._all_orders
            if q in o['item_name'].lower()
            or q in (o['supplier'] or "").lower()
            or q in (o['invoice_number'] or "").lower()
        ]
        self._populate(rows)

    def _populate(self, rows):
        tbl = self._table
        tbl.setRowCount(len(rows))
        tbl.setUpdatesEnabled(False)
        for r, o in enumerate(rows):
            tbl.setItem(r, 0, table_item(o['purchased_at'][:16].replace('T', ' ')))
            tbl.setItem(r, 1, table_item(o['item_name']))
            tbl.setItem(r, 2, centered_item(f"{o['quantity']:g}"))
            tbl.setItem(r, 3, centered_item(o['unit_abbr']))
            uc = centered_item(f"${o['unit_cost']:.2f}")
            uc.setForeground(QColor(TEXT_SECOND))
            tbl.setItem(r, 4, uc)
            tc = centered_item(f"${(o['quantity'] * o['unit_cost']):.2f}")
            tc.setForeground(QColor(ACCENT))
            tbl.setItem(r, 5, tc)
            tbl.setItem(r, 6, centered_item(o['invoice_number'] or "—"))
            tbl.setItem(r, 7, table_item(o['supplier'] or "—"))
            tbl.setItem(r, 8, table_item(o['received_by'] or "—"))
            tbl.setRowHeight(r, 36)
        tbl.setUpdatesEnabled(True)

    def _on_log(self):
        dlg = OrderDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.log_purchase(**data)
                self.refresh()
                QMessageBox.information(
                    self, "Order Logged",
                    f"Logged {data['quantity']:g} units — stock updated."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class OrderDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Incoming Order")
        self.setMinimumWidth(420)
        self._items_data = db.get_all_items()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Log Incoming Order")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)
        layout.addWidget(muted("Stock levels will be updated automatically."))
        layout.addWidget(hdivider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._item = QComboBox()
        self._item.setMinimumWidth(250)
        self._item.addItem("— Select Item —", None)
        for it in self._items_data:
            self._item.addItem(f"{it['name']}  ({it['unit_abbr']})", it['id'])
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
        self._unit_cost.setDecimals(2)
        self._unit_cost.setRange(0, 99999)
        self._unit_cost.setPrefix("$")
        form.addRow("Unit Cost:", self._unit_cost)

        self._invoice = QLineEdit()
        self._invoice.setPlaceholderText("Optional invoice / PO number")
        form.addRow("Invoice #:", self._invoice)

        self._supplier = QLineEdit()
        self._supplier.setPlaceholderText("Supplier name")
        form.addRow("Supplier:", self._supplier)

        self._received_by = QLineEdit()
        self._received_by.setPlaceholderText("Your name")
        form.addRow("Received By *:", self._received_by)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        self._notes.setPlaceholderText("Optional notes…")
        form.addRow("Notes:", self._notes)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_item_changed(self):
        item_id = self._item.currentData()
        if item_id:
            it = next((i for i in self._items_data if i['id'] == item_id), None)
            if it:
                self._unit_lbl.setText(f"{it['unit_name']} ({it['unit_abbr']})")
                if it['supplier']:
                    self._supplier.setText(it['supplier'])

    def _validate(self):
        if not self._item.currentData():
            QMessageBox.warning(self, "Missing", "Please select an item.")
            return
        if self._qty.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Quantity must be greater than 0.")
            return
        if not self._received_by.text().strip():
            QMessageBox.warning(self, "Missing", "Please enter your name.")
            return
        self.accept()

    def get_data(self):
        return {
            'item_id':        self._item.currentData(),
            'quantity':       self._qty.value(),
            'unit_cost':      self._unit_cost.value(),
            'invoice_number': self._invoice.text().strip() or None,
            'supplier':       self._supplier.text().strip() or None,
            'received_by':    self._received_by.text().strip() or None,
            'notes':          self._notes.toPlainText().strip() or None,
        }
