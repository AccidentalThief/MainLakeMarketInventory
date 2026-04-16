"""
ui/panels/prices.py
Dedicated tab to set retail prices and unit costs.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHeaderView, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

import db.database as db
from ui.widgets import (
    page_header, hdivider, make_table, table_item, centered_item, muted
)

class PricesPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        root.addWidget(page_header(
            "💲  Pricing",
            "Set retail prices for menu items, combos, and standalone goods."
        ))
        root.addWidget(hdivider())

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        # Tab 1: Menu Items & Combos
        tab_menu = QWidget()
        layout_menu = QVBoxLayout(tab_menu)
        layout_menu.addWidget(muted("Changes save automatically as you type."))
        
        self._table_menu = make_table(["Menu Item / Combo Name", "Category", "Selling Price ($)"])
        self._table_menu.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table_menu.setColumnWidth(1, 150)
        self._table_menu.setColumnWidth(2, 160)
        layout_menu.addWidget(self._table_menu)
        self._tabs.addTab(tab_menu, "🥪  Menu Items / Combos")

        # Tab 2: Standalone Items
        tab_inv = QWidget()
        layout_inv = QVBoxLayout(tab_inv)
        layout_inv.addWidget(muted("Set unit costs (COGS) and register prices for retail items."))
        
        self._table_inv = make_table(["Inventory Item Name", "Unit", "Unit Cost (COGS)", "Selling Price ($)"])
        self._table_inv.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table_inv.setColumnWidth(1, 100)
        self._table_inv.setColumnWidth(2, 160)
        self._table_inv.setColumnWidth(3, 160)
        layout_inv.addWidget(self._table_inv)
        self._tabs.addTab(tab_inv, "🛍️  Standalone Items")

    def refresh(self):
        self._load_menu_pricing()
        self._load_inv_pricing()

    def _load_menu_pricing(self):
        items = db.get_menu_items(active_only=True)
        self._table_menu.setRowCount(len(items))
        for r, mi in enumerate(items):
            self._table_menu.setItem(r, 0, table_item(mi['name']))
            self._table_menu.setItem(r, 1, table_item(mi['category'] or "—"))
            
            # Editable Selling Price
            spin = QDoubleSpinBox()
            spin.setPrefix("$ ")
            spin.setDecimals(2)
            spin.setRange(0, 9999.99)
            spin.setValue(mi.get('price', 0))
            spin.setStyleSheet("font-weight: bold; color: #4CAF50;")
            spin.valueChanged.connect(lambda val, mi_id=mi['id']: db.update_menu_item_price(mi_id, val))
            
            self._table_menu.setCellWidget(r, 2, spin)
            self._table_menu.setRowHeight(r, 48)

    def _load_inv_pricing(self):
        items = db.get_all_items()
        self._table_inv.setRowCount(len(items))
        for r, it in enumerate(items):
            self._table_inv.setItem(r, 0, table_item(it['name']))
            self._table_inv.setItem(r, 1, centered_item(it['unit_abbr']))
            
            # Editable Unit Cost (COGS)
            cost_spin = QDoubleSpinBox()
            cost_spin.setPrefix("$ ")
            cost_spin.setDecimals(2)
            cost_spin.setRange(0, 9999.99)
            cost_spin.setValue(it.get('unit_cost', 0))
            cost_spin.setStyleSheet("font-weight: bold; color: #64B5F6;")
            cost_spin.valueChanged.connect(lambda val, i_id=it['id']: db.update_item_unit_cost(i_id, val))
            self._table_inv.setCellWidget(r, 2, cost_spin)

            # Editable Selling Price
            price_spin = QDoubleSpinBox()
            price_spin.setPrefix("$ ")
            price_spin.setDecimals(2)
            price_spin.setRange(0, 9999.99)
            price_spin.setValue(it.get('selling_price', 0))
            price_spin.setStyleSheet("font-weight: bold; color: #4CAF50;")
            price_spin.valueChanged.connect(lambda val, i_id=it['id']: db.update_item_selling_price(i_id, val))
            self._table_inv.setCellWidget(r, 3, price_spin)
            
            self._table_inv.setRowHeight(r, 48)