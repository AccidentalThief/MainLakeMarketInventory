"""
ui/panels/stockcount.py
End-of-day stock count — just type in what you actually have for each item.
Saves counts and sets those as the new current quantities.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QMessageBox, QScrollArea, QFrame,
    QGridLayout, QLineEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor, QFont

import db.database as db
from ui.widgets import (
    primary_btn, secondary_btn, make_table, table_item,
    centered_item, page_header, hdivider, muted, section_title
)
from ui.styles import ACCENT, SUCCESS, WARNING, DANGER, PANEL_BG, BORDER, TEXT_SECOND


class StockCountPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count_widgets = {}   # item_id → QDoubleSpinBox
        self._items = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        save_btn = primary_btn("💾  Save Count")
        save_btn.clicked.connect(self._on_save)

        root.addWidget(page_header(
            "📋  End-of-Day Stock Count",
            "Enter the actual quantity you have on hand for each item",
            actions=[save_btn]
        ))
        root.addWidget(hdivider())

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Filter by category:"))
        self._cat_filter = QComboBox()
        self._cat_filter.setFixedWidth(160)
        self._cat_filter.addItem("All Categories", None)
        for cat in db.get_categories():
            self._cat_filter.addItem(cat['name'], cat['id'])
        self._cat_filter.currentIndexChanged.connect(self._apply_filter)
        ctrl.addWidget(self._cat_filter)

        ctrl.addSpacing(20)
        ctrl.addWidget(muted("Your name:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Who is counting?")
        self._name_input.setFixedWidth(180)
        ctrl.addWidget(self._name_input)
        ctrl.addStretch()
        root.addLayout(ctrl)

        # Scrollable count area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._count_container = QWidget()
        self._count_layout    = QVBoxLayout(self._count_container)
        self._count_layout.setContentsMargins(0, 0, 0, 0)
        self._count_layout.setSpacing(0)
        self._scroll.setWidget(self._count_container)
        root.addWidget(self._scroll, 1)

        # Tip at the bottom
        tip = muted(
            "💡 Tip: Values start at the current stock level. "
            "Just correct whatever has changed. Hit 'Save Count' when done."
        )
        tip.setWordWrap(True)
        root.addWidget(tip)

    def refresh(self):
        self._items = db.get_all_items()
        self._apply_filter()

    def _apply_filter(self):
        cat_id = self._cat_filter.currentData()
        items = [it for it in self._items
                 if cat_id is None or it['category_id'] == cat_id]
        self._rebuild_count_rows(items)

    def _rebuild_count_rows(self, items):
        # Clear old widgets
        self._count_widgets = {}
        while self._count_layout.count():
            child = self._count_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            lbl = QLabel("No items found.")
            lbl.setObjectName("Muted")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._count_layout.addWidget(lbl)
            return

        # Header row
        header = QWidget()
        header.setStyleSheet(f"background:{PANEL_BG}; border-bottom: 1px solid {BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 16, 8)
        for text, stretch in [("Item", 3), ("Category", 2), ("Current Stock", 2), ("Count on Hand", 2)]:
            lbl = QLabel(text.upper())
            lbl.setStyleSheet(f"color: {TEXT_SECOND}; font-size: 9pt; font-weight: 600;")
            hl.addWidget(lbl, stretch)
        self._count_layout.addWidget(header)

        # One row per item
        for i, item in enumerate(items):
            row_widget = QWidget()
            bg = "#2C2C2E" if i % 2 == 0 else "#242426"
            row_widget.setStyleSheet(f"background: {bg};")

            rl = QHBoxLayout(row_widget)
            rl.setContentsMargins(16, 10, 16, 10)

            name_lbl = QLabel(item['name'])
            name_lbl.setStyleSheet("font-size: 10pt;")
            rl.addWidget(name_lbl, 3)

            cat_lbl = QLabel(item['category_name'] or "—")
            cat_lbl.setStyleSheet(f"color: {TEXT_SECOND}; font-size: 9pt;")
            rl.addWidget(cat_lbl, 2)

            qty = item['current_quantity']
            thr = item['min_threshold']
            unit = item['unit_abbr']
            stock_str = f"{qty:g} {unit}"
            stock_lbl = QLabel(stock_str)
            if qty == 0:
                stock_lbl.setStyleSheet(f"color: {DANGER}; font-weight: bold;")
                stock_lbl.setText("OUT OF STOCK")
            elif qty <= thr:
                stock_lbl.setStyleSheet(f"color: {WARNING};")
            else:
                stock_lbl.setStyleSheet(f"color: {SUCCESS};")
            rl.addWidget(stock_lbl, 2)

            # Spin box starts at current qty — user just edits if it changed
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setRange(0, 99999)
            spin.setValue(qty)
            spin.setSuffix(f"  {unit}")
            spin.setFixedWidth(160)
            spin.setStyleSheet("""
                QDoubleSpinBox {
                    background: #1C1C1E;
                    border: 1px solid #3A3A3C;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10pt;
                    color: #F2F2F7;
                }
                QDoubleSpinBox:focus { border-color: #E8956D; }
            """)
            self._count_widgets[item['id']] = spin

            spin_wrapper = QHBoxLayout()
            spin_wrapper.addWidget(spin)
            spin_wrapper.addStretch()

            rl.addLayout(spin_wrapper, 2)
            self._count_layout.addWidget(row_widget)

        self._count_layout.addStretch()

    def _on_save(self):
        if not self._count_widgets:
            QMessageBox.information(self, "Nothing to Save", "No items to count.")
            return

        counted_by = self._name_input.text().strip() or None
        if not counted_by:
            reply = QMessageBox.question(
                self, "No Name",
                "You haven't entered your name. Save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        counts = [
            {'item_id': item_id, 'quantity': spin.value()}
            for item_id, spin in self._count_widgets.items()
        ]

        try:
            db.save_stock_count(counts, counted_by=counted_by)
            QMessageBox.information(
                self, "Stock Count Saved",
                f"Updated {len(counts)} item(s). Inventory is now current."
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
