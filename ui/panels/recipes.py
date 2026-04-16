"""
ui/panels/recipes.py
Manage menu items, combos, and their recipe ingredients.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
    QComboBox, QDoubleSpinBox, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt

import db.database as db
from ui.widgets import (
    primary_btn, secondary_btn, icon_btn, make_table,
    table_item, centered_item, page_header, section_title, hdivider
)

class RecipesPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mi_id = None
        self._recipe_rows = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        root.addWidget(page_header(
            "⚙  Menu & Recipes",
            "Configure the ingredients for each sandwich or combo."
        ))
        root.addWidget(hdivider())

        # Split: menu item list | ingredient editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # Left: menu item list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        add_mi_btn = primary_btn("+ New Menu Item or Combo")
        add_mi_btn.clicked.connect(self._on_add_menu_item)
        left_layout.addWidget(add_mi_btn)

        self._mi_list = make_table(["Name", "Category"])
        self._mi_list.setMaximumWidth(320)
        self._mi_list.horizontalHeader().setStretchLastSection(True)
        self._mi_list.setSelectionMode(self._mi_list.SelectionMode.SingleSelection)
        self._mi_list.itemSelectionChanged.connect(self._on_mi_selected)
        left_layout.addWidget(self._mi_list)
        splitter.addWidget(left)

        # Right: recipe editor
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        self._recipe_title = section_title("Select a menu item")
        right_layout.addWidget(self._recipe_title)

        # Ingredient row
        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self._ing_combo = QComboBox()
        add_row.addWidget(self._ing_combo, 2)

        self._ing_qty = QDoubleSpinBox()
        self._ing_qty.setDecimals(3)
        self._ing_qty.setRange(0.001, 9999)
        self._ing_qty.setValue(1)
        add_row.addWidget(self._ing_qty, 1)

        add_ing_btn = secondary_btn("Add")
        add_ing_btn.clicked.connect(self._on_add_ingredient)
        add_row.addWidget(add_ing_btn)
        right_layout.addLayout(add_row)

        self._recipe_table = make_table(["Ingredient", "Qty", "Unit", ""])
        self._recipe_table.setColumnWidth(0, 220)
        self._recipe_table.setColumnWidth(1, 80)
        self._recipe_table.setColumnWidth(2, 70)
        self._recipe_table.setColumnWidth(3, 60)
        right_layout.addWidget(self._recipe_table)

        save_btn = primary_btn("💾  Save Recipe")
        save_btn.clicked.connect(self._on_save_recipe)
        right_layout.addWidget(save_btn)

        splitter.addWidget(right)
        splitter.setSizes([300, 400])
        root.addWidget(splitter)

    def refresh(self):
        self._items_data = db.get_all_items()
        self._ing_combo.clear()
        self._ing_combo.addItem("— Select Ingredient / Item —", None)
        for it in self._items_data:
            self._ing_combo.addItem(f"{it['name']} ({it['unit_abbr']})", it['id'])
        self._load_menu_items()

    def _load_menu_items(self):
        menu_items = db.get_menu_items(active_only=False)
        tbl = self._mi_list
        tbl.setRowCount(len(menu_items))
        self._menu_items_data = menu_items
        for r, mi in enumerate(menu_items):
            tbl.setItem(r, 0, table_item(mi['name']))
            tbl.setItem(r, 1, table_item(mi['category'] or "—"))
            tbl.setRowHeight(r, 34)

    def _on_mi_selected(self):
        rows = self._mi_list.selectedItems()
        if not rows:
            return
        r  = self._mi_list.currentRow()
        mi = self._menu_items_data[r]
        self._current_mi_id = mi['id']
        self._recipe_title.setText(f"Recipe: {mi['name']}")
        
        recipe = db.get_recipe(mi['id'])
        self._recipe_rows = [
            {'item_id': ing['item_id'],
             'quantity': ing['quantity'],
             'name': ing['ingredient_name'],
             'unit': ing['unit_abbr']} 
            for ing in recipe
        ]
        self._refresh_recipe_table()

    def _refresh_recipe_table(self):
        tbl = self._recipe_table
        tbl.setRowCount(len(self._recipe_rows))
        for r, row in enumerate(self._recipe_rows):
            tbl.setItem(r, 0, table_item(row['name']))
            tbl.setItem(r, 1, centered_item(f"{row['quantity']:g}"))
            tbl.setItem(r, 2, centered_item(row['unit']))

            rem_btn = icon_btn("✕")
            rem_btn.clicked.connect(lambda _, idx=r: self._remove_ingredient(idx))
            tbl.setCellWidget(r, 3, rem_btn)
            tbl.setRowHeight(r, 34)

    def _on_add_ingredient(self):
        item_id = self._ing_combo.currentData()
        if not item_id or not self._current_mi_id:
            return
        qty  = self._ing_qty.value()
        item = next((i for i in self._items_data if i['id'] == item_id), None)
        if not item:
            return
            
        existing = next((r for r in self._recipe_rows if r['item_id'] == item_id), None)
        if existing:
            existing['quantity'] = qty
        else:
            self._recipe_rows.append({
                'item_id': item_id,
                'quantity': qty,
                'name': item['name'],
                'unit': item['unit_abbr']
            })
        self._refresh_recipe_table()

    def _remove_ingredient(self, idx: int):
        if 0 <= idx < len(self._recipe_rows):
            self._recipe_rows.pop(idx)
            self._refresh_recipe_table()

    def _on_save_recipe(self):
        if not self._current_mi_id:
            QMessageBox.warning(self, "Warning", "No menu item selected.")
            return
            
        db.save_recipe(self._current_mi_id, self._recipe_rows)
        QMessageBox.information(self, "Saved", "Recipe saved successfully.")

    def _on_add_menu_item(self):
        dlg = AddMenuItemDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_menu_item(**data)
                self._load_menu_items()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class AddMenuItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Menu Item or Combo")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addWidget(QLabel("New Menu Item / Combo"))

        form = QFormLayout()
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Turkey Club Combo")
        form.addRow("Name *:", self._name)

        self._cat = QComboBox()
        # --- NEW: Added "Combo" to the dropdown! ---
        self._cat.addItems(["Sandwich","Hot Sandwich","Combo","Ice Cream","Specialty","Other"])
        form.addRow("Category:", self._cat)
        
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Missing Info", "Please enter a name.")
            return
        self.accept()

    def get_data(self):
        return {
            'name': self._name.text().strip(), 
            'category': self._cat.currentText(),
            'price': 0.0 # Default price, configured in the Prices panel!
        }