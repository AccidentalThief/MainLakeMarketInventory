"""
ui/panels/inventory.py
Full inventory management panel — view, add, edit, deactivate items.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidgetItem, QSpinBox,
    QCheckBox, QDateEdit, QTextEdit, QScrollArea, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui  import QColor, QFont

import db.database as db
from ui.widgets  import (
    primary_btn, secondary_btn, danger_btn, icon_btn,
    make_table, table_item, centered_item, page_header,
    section_title, search_bar, hdivider, muted, stat_card
)
from ui.styles   import DANGER, WARNING, SUCCESS, ACCENT, TEXT_MUTED, INFO


class InventoryPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items = []
        self._build_ui()
        self.refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        add_btn    = primary_btn("+ Add Item")
        add_btn.clicked.connect(self._on_add_item)

        root.addWidget(page_header(
            "📦  Inventory",
            "All ingredients and goods",
            actions=[add_btn]
        ))
        root.addWidget(hdivider())

        # Search + filter row
        top_row = QHBoxLayout()
        self._search = search_bar("Search items…")
        self._search.textChanged.connect(self._filter)
        top_row.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.setFixedWidth(160)
        self._cat_filter.addItem("All Categories", None)
        for cat in db.get_categories():
            self._cat_filter.addItem(cat['name'], cat['id'])
        self._cat_filter.currentIndexChanged.connect(self._filter)
        top_row.addWidget(QLabel("Category:"))
        top_row.addWidget(self._cat_filter)

        self._low_only = QCheckBox("Low Stock Only")
        self._low_only.stateChanged.connect(self._filter)
        top_row.addWidget(self._low_only)
        top_row.addStretch()
        root.addLayout(top_row)

        # Table
        cols = ["Item Name", "Category", "Stock", "Unit",
                "Threshold", "Supplier", "Actions"]
        self._table = make_table(cols)
        
        # Take control of the column widths and stretching
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 'Item Name' stretches to fill empty space
        header.setStretchLastSection(False)

        # Set fixed widths for the rest of the columns
        self._table.setColumnWidth(1, 140)  # Category
        self._table.setColumnWidth(2, 110)  # Stock
        self._table.setColumnWidth(3, 80)   # Unit
        self._table.setColumnWidth(4, 100)  # Threshold
        self._table.setColumnWidth(5, 140)  # Supplier
        self._table.setColumnWidth(6, 120)  # Actions (Prevents buttons from getting cut off)
        
        root.addWidget(self._table)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._all_items = db.get_all_items()
        self._filter()

    def _filter(self):
        q        = self._search.text().lower()
        cat_id   = self._cat_filter.currentData()
        low_only = self._low_only.isChecked()

        items = [
            it for it in self._all_items
            if (q in it['name'].lower())
            and (cat_id is None or it['category_id'] == cat_id)
            and (not low_only or it['current_quantity'] <= it['min_threshold'])
        ]
        self._populate_table(items)

    def _populate_table(self, items: list):
        tbl = self._table
        tbl.setRowCount(len(items))
        tbl.setUpdatesEnabled(False)

        for r, item in enumerate(items):
            qty   = item['current_quantity']
            thr   = item['min_threshold']
            unit  = item['unit_abbr']

            tbl.setItem(r, 0, table_item(item['name']))
            tbl.setItem(r, 1, table_item(item['category_name'] or "—"))

            # Stock cell with color
            qty_str = f"{qty:g} {unit}"
            qi = centered_item(qty_str)
            if qty == 0:
                qi.setForeground(QColor(DANGER))
                qi.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif qty <= thr:
                qi.setForeground(QColor(WARNING))
            else:
                qi.setForeground(QColor(SUCCESS))
            tbl.setItem(r, 2, qi)

            tbl.setItem(r, 3, centered_item(unit))
            tbl.setItem(r, 4, centered_item(f"{thr:g}"))
            tbl.setItem(r, 5, table_item(item['supplier'] or "—"))

            # Action buttons cell
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)

            edit_btn = icon_btn("✏ Edit")
            edit_btn.setProperty("item_id", item['id'])
            edit_btn.clicked.connect(lambda _, i=item: self._on_edit_item(i))

            del_btn = icon_btn("🗑")
            del_btn.setToolTip("Deactivate item")
            del_btn.clicked.connect(lambda _, i=item: self._on_deactivate(i))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            tbl.setCellWidget(r, 6, action_widget)

            tbl.setRowHeight(r, 40)

        tbl.setUpdatesEnabled(True)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_add_item(self):
        dlg = ItemDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_item(**data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_edit_item(self, item: dict):
        dlg = ItemDialog(item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.update_item(item['id'], **data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_deactivate(self, item: dict):
        reply = QMessageBox.question(
            self, "Deactivate Item",
            f"Hide '{item['name']}' from active inventory?\n"
            "It will be preserved in historical records.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.update_item(item['id'], is_active=0)
            self.refresh()


# ── Item Add / Edit Dialog ────────────────────────────────────────────────────

class ItemDialog(QDialog):

    def __init__(self, item: dict = None, parent=None):
        super().__init__(parent)
        self._item = item
        self.setWindowTitle("Edit Item" if item else "Add New Item")
        self.setMinimumWidth(420)
        self._build_ui()
        if item:
            self._populate(item)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = "Edit Item" if self._item else "Add New Item"
        lbl = QLabel(title)
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

        self._threshold = QDoubleSpinBox()
        self._threshold.setDecimals(2)
        self._threshold.setRange(0, 99999)
        self._threshold.setSuffix("  (low-stock trigger)")
        form.addRow("Min Threshold *:", self._threshold)

        self._reorder = QDoubleSpinBox()
        self._reorder.setDecimals(2)
        self._reorder.setRange(0, 99999)
        form.addRow("Reorder Qty:", self._reorder)

        self._par = QDoubleSpinBox()
        self._par.setDecimals(2)
        self._par.setRange(0, 99999)
        form.addRow("Par Level:", self._par)

        self._supplier = QLineEdit()
        self._supplier.setPlaceholderText("Supplier name or contact")
        form.addRow("Supplier:", self._supplier)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(72)
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

    def _populate(self, item: dict):
        self._name.setText(item['name'])
        self._threshold.setValue(item['min_threshold'])
        self._reorder.setValue(item['reorder_quantity'] or 0)
        self._par.setValue(item['par_level'] or 0)
        self._supplier.setText(item['supplier'] or "")
        self._notes.setPlainText(item['notes'] or "")

        # Set category combo
        for i in range(self._category.count()):
            if self._category.itemData(i) == item['category_id']:
                self._category.setCurrentIndex(i)
                break

        # Set unit combo
        for i in range(self._unit.count()):
            if self._unit.itemData(i) == item['unit_id']:
                self._unit.setCurrentIndex(i)
                break

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Item name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'name':            self._name.text().strip(),
            'category_id':     self._category.currentData(),
            'unit_id':         self._unit.currentData(),
            'min_threshold':   self._threshold.value(),
            'reorder_quantity':self._reorder.value() or None,
            'par_level':       self._par.value() or None,
            'supplier':        self._supplier.text().strip() or None,
            'notes':           self._notes.toPlainText().strip() or None,
        }
