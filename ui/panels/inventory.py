"""
ui/panels/inventory.py  –  Simplified
View all items and their current stock. Add / edit items.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QCheckBox, QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor, QFont

import db.database as db
from ui.widgets import (
    primary_btn, secondary_btn, icon_btn, make_table,
    table_item, centered_item, page_header, search_bar, hdivider, muted
)
from ui.styles import DANGER, WARNING, SUCCESS, ACCENT


class InventoryPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        add_btn = primary_btn("+ Add Item")
        add_btn.clicked.connect(self._on_add)

        root.addWidget(page_header(
            "📦  Inventory",
            "All items and current stock levels",
            actions=[add_btn]
        ))
        root.addWidget(hdivider())

        # Search + filter row
        row = QHBoxLayout()
        self._search = search_bar("Search items…")
        self._search.textChanged.connect(self._filter)
        row.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.setFixedWidth(160)
        self._cat_filter.addItem("All Categories", None)
        for cat in db.get_categories():
            self._cat_filter.addItem(cat['name'], cat['id'])
        self._cat_filter.currentIndexChanged.connect(self._filter)
        row.addWidget(QLabel("Category:"))
        row.addWidget(self._cat_filter)

        self._low_only = QCheckBox("Low Stock Only")
        self._low_only.stateChanged.connect(self._filter)
        row.addWidget(self._low_only)
        row.addStretch()
        root.addLayout(row)

        # Table
        self._table = make_table(
            ["Item Name", "Category", "Stock", "Unit", "Low-Stock Alert", "Supplier", "Actions"]
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)
        self._table.setColumnWidth(1, 140)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 70)
        self._table.setColumnWidth(4, 130)
        self._table.setColumnWidth(5, 140)
        self._table.setColumnWidth(6, 110)
        root.addWidget(self._table)

    def refresh(self):
        self._all_items = db.get_all_items()
        self._filter()

    def _filter(self):
        q      = self._search.text().lower()
        cat_id = self._cat_filter.currentData()
        low    = self._low_only.isChecked()
        items  = [
            it for it in self._all_items
            if (q in it['name'].lower())
            and (cat_id is None or it['category_id'] == cat_id)
            and (not low or it['current_quantity'] <= it['min_threshold'])
        ]
        self._populate(items)

    def _populate(self, items):
        tbl = self._table
        tbl.setRowCount(len(items))
        tbl.setUpdatesEnabled(False)
        for r, item in enumerate(items):
            qty = item['current_quantity']
            thr = item['min_threshold']
            unit = item['unit_abbr']

            tbl.setItem(r, 0, table_item(item['name']))
            tbl.setItem(r, 1, table_item(item['category_name'] or "—"))

            qi = centered_item(f"{qty:g} {unit}")
            if qty == 0:
                qi.setForeground(QColor(DANGER))
                qi.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                qi.setText("OUT OF STOCK")
            elif qty <= thr:
                qi.setForeground(QColor(WARNING))
            else:
                qi.setForeground(QColor(SUCCESS))
            tbl.setItem(r, 2, qi)

            tbl.setItem(r, 3, centered_item(unit))
            tbl.setItem(r, 4, centered_item(f"{thr:g} {unit}" if thr else "—"))
            tbl.setItem(r, 5, table_item(item['supplier'] or "—"))

            # Actions
            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            eb = icon_btn("✏ Edit")
            eb.clicked.connect(lambda _, i=item: self._on_edit(i))
            db_btn = icon_btn("🗑")
            db_btn.setToolTip("Deactivate item")
            db_btn.clicked.connect(lambda _, i=item: self._on_deactivate(i))
            al.addWidget(eb)
            al.addWidget(db_btn)
            tbl.setCellWidget(r, 6, aw)
            tbl.setRowHeight(r, 40)
        tbl.setUpdatesEnabled(True)

    def _on_add(self):
        dlg = ItemDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_item(**data)
                self.refresh()
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    QMessageBox.warning(self, "Duplicate", f"'{data['name']}' already exists.")
                else:
                    QMessageBox.critical(self, "Error", str(e))

    def _on_edit(self, item):
        dlg = ItemDialog(item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.update_item(item['id'], **data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_deactivate(self, item):
        reply = QMessageBox.question(
            self, "Deactivate", f"Hide '{item['name']}' from active inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.update_item(item['id'], is_active=0)
            self.refresh()


class ItemDialog(QDialog):

    def __init__(self, item=None, parent=None):
        super().__init__(parent)
        self._item = item
        self.setWindowTitle("Edit Item" if item else "Add New Item")
        self.setMinimumWidth(400)
        self._build_ui()
        if item:
            self._populate(item)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Edit Item" if self._item else "Add New Item")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)
        layout.addWidget(hdivider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Sliced Turkey")
        form.addRow("Name *:", self._name)

        self._category = QComboBox()
        self._category.addItem("— Select —", None)
        for cat in db.get_categories():
            self._category.addItem(cat['name'], cat['id'])
        form.addRow("Category:", self._category)

        self._unit = QComboBox()
        for u in db.get_units():
            self._unit.addItem(f"{u['name']} ({u['abbreviation']})", u['id'])
        form.addRow("Unit *:", self._unit)

        self._qty = QDoubleSpinBox()
        self._qty.setDecimals(2)
        self._qty.setRange(0, 99999)
        if self._item:
            self._qty.setEnabled(False)
            self._qty.setToolTip("Adjust stock via Orders or Stock Count.")
        form.addRow("Current Stock:" if self._item else "Initial Stock:", self._qty)

        self._threshold = QDoubleSpinBox()
        self._threshold.setDecimals(2)
        self._threshold.setRange(0, 99999)
        self._threshold.setSuffix("  (low-stock alert)")
        form.addRow("Alert Threshold:", self._threshold)

        self._supplier = QLineEdit()
        self._supplier.setPlaceholderText("Supplier name")
        form.addRow("Supplier:", self._supplier)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(64)
        self._notes.setPlaceholderText("Optional notes…")
        form.addRow("Notes:", self._notes)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, item):
        self._name.setText(item['name'])
        self._qty.setValue(item.get('current_quantity', 0))
        self._threshold.setValue(item['min_threshold'])
        self._supplier.setText(item['supplier'] or "")
        self._notes.setPlainText(item['notes'] or "")
        for i in range(self._category.count()):
            if self._category.itemData(i) == item['category_id']:
                self._category.setCurrentIndex(i)
                break
        for i in range(self._unit.count()):
            if self._unit.itemData(i) == item['unit_id']:
                self._unit.setCurrentIndex(i)
                break

    def _validate(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Missing", "Please enter an item name.")
            return
        if not self._unit.currentData():
            QMessageBox.warning(self, "Missing", "Please select a unit.")
            return
        self.accept()

    def get_data(self):
        return {
            'name':             self._name.text().strip(),
            'category_id':      self._category.currentData(),
            'unit_id':          self._unit.currentData(),
            'current_quantity': self._qty.value(),
            'min_threshold':    self._threshold.value(),
            'supplier':         self._supplier.text().strip() or None,
            'notes':            self._notes.toPlainText().strip() or None,
        }
