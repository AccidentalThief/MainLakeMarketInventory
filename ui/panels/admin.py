"""
ui/panels/admin.py  –  Simplified
Password-protected admin panel to undo mistakes and manage settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QStackedWidget, QMessageBox, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt

import db.database as db
from ui.widgets import (
    primary_btn, danger_btn, secondary_btn, icon_btn,
    page_header, hdivider, make_table, table_item, centered_item, muted
)
from ui.styles import SUCCESS, INFO, WARNING, ACCENT


class AdminPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._login_screen = self._build_login_screen()
        self._tools_screen = self._build_tools_screen()
        self._stack.addWidget(self._login_screen)
        self._stack.addWidget(self._tools_screen)

    # ── Login ─────────────────────────────────────────────────────────────────

    def _build_login_screen(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        lock = QLabel("🔒")
        lock.setStyleSheet("font-size: 48pt;")
        lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lock)

        title = QLabel("Admin Access Required")
        title.setObjectName("H1")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = muted("Enter the admin password to fix mistakes and manage settings.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pass_input = QLineEdit()
        self._pass_input.setPlaceholderText("Password…")
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_input.setFixedWidth(240)
        self._pass_input.returnPressed.connect(self._try_login)
        row.addWidget(self._pass_input)

        unlock_btn = primary_btn("Unlock")
        unlock_btn.clicked.connect(self._try_login)
        row.addWidget(unlock_btn)

        layout.addLayout(row)

        return w

    def _try_login(self):
        if db.verify_admin(self._pass_input.text()):
            self._pass_input.clear()
            self._stack.setCurrentWidget(self._tools_screen)
            self.refresh()
        else:
            QMessageBox.critical(self, "Access Denied", "Incorrect password.")
            self._pass_input.clear()

    # ── Tools ─────────────────────────────────────────────────────────────────

    def _build_tools_screen(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        lock_btn = secondary_btn("🔒 Lock Session")
        lock_btn.clicked.connect(lambda: self._stack.setCurrentWidget(self._login_screen))

        layout.addWidget(page_header(
            "🛡️  Admin Tools",
            "Undo employee mistakes and manage system settings.",
            actions=[lock_btn]
        ))
        layout.addWidget(hdivider())

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_undo_tab(), "↩  Undo Mistakes")
        self._tabs.addTab(self._build_settings_tab(), "⚙  Settings")

        return w

    def _build_undo_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Recent Orders & Stock Counts").setObjectName("H2") or
                         self._h2("Recent Orders & Stock Counts"))
        layout.addWidget(muted(
            "Undoing an order removes it from history and subtracts the quantity from stock. "
            "Undoing a stock count re-applies the previous count."
        ))

        self._history_table = make_table(["Type", "Date", "Details", "Undo"])
        self._history_table.setColumnWidth(0, 110)
        self._history_table.setColumnWidth(1, 155)
        self._history_table.setColumnWidth(3, 90)
        layout.addWidget(self._history_table)
        return tab

    def _build_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)

        layout.addWidget(self._h2("Change Admin Password"))
        pwd_btn = secondary_btn("Update Password")
        pwd_btn.setFixedWidth(200)
        pwd_btn.clicked.connect(self._change_password)
        layout.addWidget(pwd_btn)

        layout.addWidget(hdivider())

        layout.addWidget(self._h2("Danger Zone"))
        layout.addWidget(muted("Permanently deletes ALL items and history. Cannot be undone."))
        reset_btn = danger_btn("🧨  Factory Reset Database")
        reset_btn.setFixedWidth(260)
        reset_btn.clicked.connect(self._factory_reset)
        layout.addWidget(reset_btn)

        return tab

    def _h2(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("H2")
        return lbl

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        if self._stack.currentWidget() != self._tools_screen:
            return

        tbl = self._history_table
        tbl.setRowCount(0)
        row_idx = 0

        # Recent orders (purchases)
        for p in db.get_purchase_history(limit=30):
            tbl.insertRow(row_idx)
            type_lbl = centered_item("Order")
            type_lbl.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor(ACCENT))
            tbl.setItem(row_idx, 0, type_lbl)
            tbl.setItem(row_idx, 1, table_item(p['purchased_at'][:16].replace('T', ' ')))
            tbl.setItem(row_idx, 2, table_item(
                f"{p['received_by'] or 'Unknown'} logged {p['quantity']:g} {p['unit_abbr']} of {p['item_name']}"
            ))
            btn = icon_btn("↩ Undo")
            btn.clicked.connect(lambda _, pid=p['id']: self._undo_purchase(pid))
            tbl.setCellWidget(row_idx, 3, btn)
            tbl.setRowHeight(row_idx, 38)
            row_idx += 1

        # Recent stock counts
        for sc in db.get_stock_count_history(limit=30):
            tbl.insertRow(row_idx)
            type_lbl = centered_item("Count")
            type_lbl.setForeground(__import__('PyQt6.QtGui', fromlist=['QColor']).QColor(INFO))
            tbl.setItem(row_idx, 0, type_lbl)
            tbl.setItem(row_idx, 1, table_item(sc['counted_at'][:16].replace('T', ' ')))
            tbl.setItem(row_idx, 2, table_item(
                f"{sc['counted_by'] or 'Unknown'} counted {sc['quantity']:g} {sc['unit_abbr']} of {sc['item_name']}"
            ))
            # Stock counts can't be simply "undone" to a prior state,
            # so offer a note button instead
            note = icon_btn("ℹ Info")
            note.clicked.connect(lambda _, s=sc: QMessageBox.information(
                self, "Stock Count Entry",
                f"Item: {s['item_name']}\n"
                f"Counted: {s['quantity']:g} {s['unit_abbr']}\n"
                f"By: {s['counted_by'] or 'Unknown'}\n"
                f"At: {s['counted_at'][:16]}\n\n"
                "To correct this, simply run a new Stock Count with the right number."
            ))
            tbl.setCellWidget(row_idx, 3, note)
            tbl.setRowHeight(row_idx, 38)
            row_idx += 1

    # ── Actions ───────────────────────────────────────────────────────────────

    def _undo_purchase(self, purchase_id):
        reply = QMessageBox.question(
            self, "Undo Order",
            "This will delete the order record and subtract that quantity from stock.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.undo_purchase(purchase_id)
                self.refresh()
                QMessageBox.information(self, "Done", "Order undone and stock adjusted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _change_password(self):
        new_pass, ok = QInputDialog.getText(
            self, "Change Password", "New admin password:",
            QLineEdit.EchoMode.Password
        )
        if ok and new_pass.strip():
            db.change_admin_password(new_pass.strip())
            QMessageBox.information(self, "Updated", "Password changed successfully.")

    def _factory_reset(self):
        text, ok = QInputDialog.getText(
            self, "Confirm Reset",
            "⚠  This wipes ALL items and history.\n\nType RESET to confirm:"
        )
        if ok and text == "RESET":
            try:
                db.factory_reset_database()
                QMessageBox.information(self, "Done", "Database has been reset.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
