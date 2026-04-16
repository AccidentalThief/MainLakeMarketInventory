"""
ui/panels/sales.py
Log sandwich / menu item sales → auto-deducts recipe ingredients.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidgetItem,
    QTextEdit, QScrollArea, QSplitter, QGroupBox
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

        manage_btn = secondary_btn("⚙  Manage Recipes")
        manage_btn.clicked.connect(self._on_manage_recipes)

        root.addWidget(page_header(
            "🥪  Sales & Usage",
            "Log menu item sales — ingredients deducted automatically",
            actions=[manage_btn, log_btn]
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

        cols = ["Date/Time", "Menu Item", "Category", "Qty Sold",
                "Logged By", "Notes"]
        self._table = make_table(cols)
        self._table.setColumnWidth(0, 150)
        self._table.setColumnWidth(1, 200)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 80)
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

        total_items  = sum(s['quantity_sold'] for s in self._sales)
        unique_items = len({s['menu_item_id'] for s in self._sales})

        self._stats_row.addWidget(
            stat_card("Total Sold", str(total_items), ACCENT))
        self._stats_row.addWidget(
            stat_card("Menu Items", str(unique_items), INFO))
        self._stats_row.addStretch()

    def _filter(self):
        q = self._search.text().lower()
        rows = [s for s in self._sales
                if q in s['menu_item_name'].lower()
                or q in (s['logged_by'] or "").lower()]
        self._populate_table(rows)

    def _populate_table(self, rows: list):
        tbl = self._table
        tbl.setRowCount(len(rows))
        tbl.setUpdatesEnabled(False)
        for r, s in enumerate(rows):
            date_str = s['sold_at'][:16].replace('T', ' ')
            tbl.setItem(r, 0, table_item(date_str))
            tbl.setItem(r, 1, table_item(s['menu_item_name']))
            tbl.setItem(r, 2, table_item(s['category'] or "—"))
            tbl.setItem(r, 3, centered_item(str(s['quantity_sold'])))
            tbl.setItem(r, 4, table_item(s['logged_by'] or "—"))
            tbl.setItem(r, 5, table_item(s['notes'] or "—"))
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
                    "Sale recorded and inventory updated."
                )
            except ValueError as e:
                QMessageBox.warning(self, "Recipe Missing", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_manage_recipes(self):
        dlg = RecipeManagerDialog(parent=self)
        dlg.exec()
        self.refresh()


# ── Log Sale Dialog ───────────────────────────────────────────────────────────

class SaleDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Sale")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("Log Menu Item Sale")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)

        sub = muted("Ingredients will be automatically deducted from inventory.")
        layout.addWidget(sub)

        # Recipe preview
        self._preview_frame = QFrame()
        self._preview_frame.setObjectName("Card")
        pv_layout = QVBoxLayout(self._preview_frame)
        pv_layout.setContentsMargins(12, 10, 12, 10)
        self._preview_label = QLabel("Select a menu item to preview ingredients")
        self._preview_label.setObjectName("Muted")
        self._preview_label.setWordWrap(True)
        pv_layout.addWidget(self._preview_label)
        layout.addWidget(self._preview_frame)

        layout.addWidget(hdivider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._menu_item = QComboBox()
        self._menu_item.setMinimumWidth(260)
        self._menu_item.addItem("— Select Menu Item —", None)
        for mi in db.get_menu_items():
            self._menu_item.addItem(f"{mi['name']}  [{mi['category']}]", mi['id'])
        self._menu_item.currentIndexChanged.connect(self._update_preview)
        form.addRow("Menu Item *:", self._menu_item)

        self._qty = QSpinBox()
        self._qty.setRange(1, 999)
        self._qty.setValue(1)
        form.addRow("Quantity *:", self._qty)

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
        if not self._menu_item.currentData():
            QMessageBox.warning(self, "Validation", "Please select a menu item.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'menu_item_id':  self._menu_item.currentData(),
            'quantity_sold': self._qty.value(),
            'logged_by':     self._logged_by.text().strip() or None,
            'notes':         self._notes.toPlainText().strip() or None,
        }


# ── Recipe Manager Dialog ─────────────────────────────────────────────────────

class RecipeManagerDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recipe Manager")
        self.setMinimumSize(680, 520)
        self._items_data = db.get_all_items()
        self._build_ui()
        self._load_menu_items()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel("⚙  Recipe Manager")
        lbl.setObjectName("H2")
        layout.addWidget(lbl)

        sub = muted("Configure the ingredients for each menu item.")
        layout.addWidget(sub)
        layout.addWidget(hdivider())

        # Split: menu item list | ingredient editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # Left: menu item list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        add_mi_btn = primary_btn("+ New Menu Item")
        add_mi_btn.clicked.connect(self._on_add_menu_item)
        left_layout.addWidget(add_mi_btn)

        self._mi_list = make_table(["Name", "Category"])
        self._mi_list.setMaximumWidth(280)
        self._mi_list.horizontalHeader().setStretchLastSection(True)
        self._mi_list.setSelectionMode(
            self._mi_list.SelectionMode.SingleSelection)
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
        self._ing_combo.addItem("— Select Ingredient —", None)
        for it in self._items_data:
            self._ing_combo.addItem(
                f"{it['name']} ({it['unit_abbr']})", it['id'])
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
        splitter.setSizes([260, 400])
        layout.addWidget(splitter)

        close_btn = secondary_btn("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._current_mi_id = None
        self._recipe_rows   = []   # list of {item_id, quantity}

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
        # Check duplicate
        existing = next((r for r in self._recipe_rows
                        if r['item_id'] == item_id), None)
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
            name, cat = dlg.get_data()
            try:
                db.add_menu_item(name, cat)
                self._load_menu_items()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class AddMenuItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Menu Item")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addWidget(QLabel("New Menu Item"))

        form = QFormLayout()
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Turkey Club")
        form.addRow("Name *:", self._name)

        self._cat = QComboBox()
        self._cat.addItems(["Sandwich","Hot Sandwich","Ice Cream","Specialty","Other"])
        form.addRow("Category:", self._cat)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return self._name.text().strip(), self._cat.currentText()
