"""
ui/panels/sales.py
Log sandwich / menu item sales → auto-deducts recipe ingredients,
or log direct sales of standalone retail items (drinks, chips, etc.).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidgetItem,
    QTextEdit, QScrollArea, QSplitter, QGroupBox,
    QRadioButton, QButtonGroup, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor, QFont

import db.database as db
from ui.widgets  import (
    primary_btn, secondary_btn, icon_btn,
    make_table, table_item, centered_item, page_header,
    section_title, search_bar, hdivider, muted, stat_card
)
from ui.styles   import DANGER, WARNING, SUCCESS, ACCENT, INFO, TEXT_SECOND


class SalesPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        log_btn = primary_btn("+ Log Sale")
        log_btn.clicked.connect(self._on_log_sale)

        root.addWidget(page_header(
            "🥪  Sales & Usage",
            "Log sales of prepared recipes or standalone items",
            actions=[log_btn]
        ))
        root.addWidget(hdivider())

        # Stats
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(12)
        root.addLayout(self._stats_row)

        # Filter row
        row = QHBoxLayout()
        self._search = search_bar("Search sales…")
        self._search.textChanged.connect(self._filter)
        row.addWidget(self._search)

        row.addWidget(QLabel("Period:"))
        self._period = QComboBox()
        self._period.addItems(["Today","Last 7 days","Last 30 days"])
        self._period.setCurrentIndex(1)
        self._period.currentIndexChanged.connect(self.refresh)
        self._period.setFixedWidth(130)
        row.addWidget(self._period)
        row.addStretch()
        root.addLayout(row)

        # Added Revenue Column
        cols = ["Date/Time", "Item Sold", "Qty", "COGS", "Revenue", "Logged By"]
        self._table = make_table(cols)
        self._table.setColumnWidth(0, 150)
        self._table.setColumnWidth(1, 200)
        self._table.setColumnWidth(2, 60)
        self._table.setColumnWidth(3, 90) # COGS
        self._table.setColumnWidth(4, 90) # Revenue
        root.addWidget(self._table)

    def refresh(self):
        days_map = {0: 1, 1: 7, 2: 30}
        days = days_map[self._period.currentIndex()]
        self._sales = db.get_sales_history(days=days)
        self._rebuild_stats()
        self._filter()

    def _rebuild_stats(self):
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_items = sum(s['quantity_sold'] for s in self._sales)
        total_cogs  = sum(s.get('cogs', 0) for s in self._sales)
        total_rev   = sum(s.get('revenue', 0) for s in self._sales)
        profit      = total_rev - total_cogs # Gross Profit!

        self._stats_row.addWidget(
            stat_card("Total Sold", str(total_items), ACCENT))
        self._stats_row.addWidget(
            stat_card("Total Revenue", f"${total_rev:,.2f}", SUCCESS))
        self._stats_row.addWidget(
            stat_card("Total COGS", f"${total_cogs:,.2f}", INFO)) 
        self._stats_row.addWidget(
            stat_card("Gross Profit", f"${profit:,.2f}", WARNING))
            
        self._stats_row.addStretch()

    def _filter(self):
        q = self._search.text().lower()
        rows = [s for s in self._sales
                if q in (s['menu_item_name'] or "").lower()
                or q in (s['logged_by'] or "").lower()]
        self._populate_table(rows)

    def _populate_table(self, rows: list):
        tbl = self._table
        tbl.setRowCount(len(rows))
        tbl.setUpdatesEnabled(False)
        for r, s in enumerate(rows):
            date_str = s['sold_at'][:16].replace('T', ' ')
            tbl.setItem(r, 0, table_item(date_str))
            
            name_str = s['menu_item_name'] or "—"
            if s.get('item_id'):  
                name_str = f"🛍️ {name_str}"
                
            tbl.setItem(r, 1, table_item(name_str))
            tbl.setItem(r, 2, centered_item(str(s['quantity_sold'])))
            
            cogs_item = centered_item(f"${s.get('cogs', 0):.2f}")
            cogs_item.setForeground(QColor(INFO))
            tbl.setItem(r, 3, cogs_item)
            
            rev_item = centered_item(f"${s.get('revenue', 0):.2f}")
            rev_item.setForeground(QColor(SUCCESS))
            tbl.setItem(r, 4, rev_item)
            
            tbl.setItem(r, 5, table_item(s['logged_by'] or "—"))
            tbl.setRowHeight(r, 36)
        tbl.setUpdatesEnabled(True)

    def _on_log_sale(self):
        dlg = SaleDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.log_sale(**data)
                self.refresh()
                QMessageBox.information(
                    self, "Sale Logged",
                    "Sale recorded, inventory updated, and revenue tracked."
                )
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


# ── Log Sale Dialog ───────────────────────────────────────────────────────────

class SaleDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Sale")
        self.setMinimumWidth(460)
        self._items_data = db.get_all_items()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("Log Sale")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)

        sub = muted("Inventory will be automatically deducted based on the item type.")
        layout.addWidget(sub)
        
        # --- Type Selection ---
        self._type_group = QButtonGroup(self)
        row_radios = QHBoxLayout()
        
        self._radio_menu = QRadioButton("Prepared Recipe (Sandwiches)")
        self._radio_inv = QRadioButton("Standalone Item (Drinks, Chips)")
        self._radio_menu.setChecked(True)
        
        self._type_group.addButton(self._radio_menu)
        self._type_group.addButton(self._radio_inv)
        
        row_radios.addWidget(self._radio_menu)
        row_radios.addWidget(self._radio_inv)
        layout.addLayout(row_radios)
        
        layout.addWidget(hdivider())

        # --- Dynamic Stack ---
        self._stack = QStackedWidget()
        
        # Page 0: Prepared Recipe 
        page_menu = QWidget()
        form_menu = QFormLayout(page_menu)
        form_menu.setContentsMargins(0, 0, 0, 0)
        form_menu.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self._menu_item = QComboBox()
        self._menu_item.setMinimumWidth(260)
        self._menu_item.addItem("— Select Menu Item —", None)
        for mi in db.get_menu_items():
            self._menu_item.addItem(f"{mi['name']}  [{mi['category']}]", mi['id'])
        self._menu_item.currentIndexChanged.connect(self._update_preview)
        form_menu.addRow("Menu Item *:", self._menu_item)
        
        self._preview_label = QLabel("Select a menu item to preview ingredients")
        self._preview_label.setObjectName("Muted")
        self._preview_label.setWordWrap(True)
        form_menu.addRow("", self._preview_label)
        
        self._stack.addWidget(page_menu)
        
        # Page 1: Standalone Inventory Item
        page_inv = QWidget()
        form_inv = QFormLayout(page_inv)
        form_inv.setContentsMargins(0, 0, 0, 0)
        form_inv.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self._inv_item = QComboBox()
        self._inv_item.setMinimumWidth(260)
        self._inv_item.addItem("— Select Standalone Item —", None)
        for it in self._items_data:
            self._inv_item.addItem(f"{it['name']} ({it['unit_abbr']})  —  Stock: {it['current_quantity']:g}", it['id'])
        form_inv.addRow("Inventory Item *:", self._inv_item)
        
        self._stack.addWidget(page_inv)
        layout.addWidget(self._stack)

        # Toggle connection
        self._radio_menu.toggled.connect(self._on_type_changed)

        # --- Common Fields ---
        form_common = QFormLayout()
        form_common.setContentsMargins(0, 0, 0, 0)
        form_common.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._qty = QSpinBox()
        self._qty.setRange(1, 9999)
        self._qty.setValue(1)
        form_common.addRow("Quantity Sold *:", self._qty)

        self._logged_by = QLineEdit()
        self._logged_by.setPlaceholderText("Your name")
        form_common.addRow("Logged By:", self._logged_by)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        self._notes.setPlaceholderText("Optional notes…")
        form_common.addRow("Notes:", self._notes)

        layout.addLayout(form_common)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_type_changed(self):
        if self._radio_menu.isChecked():
            self._stack.setCurrentIndex(0)
        else:
            self._stack.setCurrentIndex(1)

    def _update_preview(self):
        mi_id = self._menu_item.currentData()
        if not mi_id:
            self._preview_label.setText("Select a menu item to preview ingredients")
            return
        recipe = db.get_recipe(mi_id)
        if not recipe:
            self._preview_label.setText("⚠  No recipe configured for this item.")
            return
        lines = ["Ingredients per item:"]
        for ing in recipe:
            lines.append(f"  • {ing['quantity']:g} {ing['unit_abbr']}  {ing['ingredient_name']}")
        self._preview_label.setText("\n".join(lines))

    def _validate_and_accept(self):
        if self._radio_menu.isChecked() and not self._menu_item.currentData():
            QMessageBox.warning(self, "Missing Info", "Please select a menu item.")
            return
        if self._radio_inv.isChecked() and not self._inv_item.currentData():
            QMessageBox.warning(self, "Missing Info", "Please select an inventory item.")
            return
        if not self._logged_by.text().strip():
            QMessageBox.warning(self, "Missing Info", "Please enter your name in 'Logged By'.")
            return
            
        self.accept()

    def get_data(self) -> dict:
        return {
            'menu_item_id':  self._menu_item.currentData() if self._radio_menu.isChecked() else None,
            'item_id':       self._inv_item.currentData() if self._radio_inv.isChecked() else None,
            'quantity_sold': self._qty.value(),
            'logged_by':     self._logged_by.text().strip() or None,
            'notes':         self._notes.toPlainText().strip() or None,
        }