from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QStackedWidget, QMessageBox, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import db.database as db
from ui.widgets import (
    primary_btn, danger_btn, secondary_btn, page_header, hdivider, 
    make_table, table_item, centered_item, muted, icon_btn
)
from ui.styles import SUCCESS, INFO

class AdminPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # Build the two screens
        self._login_screen = self._build_login_screen()
        self._tools_screen = self._build_tools_screen()

        self._stack.addWidget(self._login_screen)
        self._stack.addWidget(self._tools_screen)

    # ── Login Screen ──────────────────────────────────────────────────────────

    def _build_login_screen(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        lock_icon = QLabel("🔒")
        lock_icon.setStyleSheet("font-size: 48pt;")
        lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lock_icon)

        title = QLabel("Admin Access Required")
        title.setObjectName("H1")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = muted("Please enter the admin password to manage records and system settings.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._pass_input = QLineEdit()
        self._pass_input.setPlaceholderText("Password...")
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_input.setFixedWidth(250)
        self._pass_input.returnPressed.connect(self._try_login)
        input_row.addWidget(self._pass_input)

        login_btn = primary_btn("Unlock")
        login_btn.clicked.connect(self._try_login)
        input_row.addWidget(login_btn)

        layout.addLayout(input_row)
        return w

    def _try_login(self):
        pwd = self._pass_input.text()
        if db.verify_admin(pwd):
            self._pass_input.clear()
            self._stack.setCurrentWidget(self._tools_screen)
            self.refresh()
        else:
            QMessageBox.critical(self, "Access Denied", "Incorrect password.")
            self._pass_input.clear()

    def _lock_system(self):
        self._stack.setCurrentWidget(self._login_screen)

    # ── Tools Screen ──────────────────────────────────────────────────────────

    def _build_tools_screen(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        lock_btn = secondary_btn("🔒 Lock Session")
        lock_btn.clicked.connect(self._lock_system)

        layout.addWidget(page_header(
            "🛡️ Admin Tools",
            "Fix mistakes and manage system configuration.",
            actions=[lock_btn]
        ))
        layout.addWidget(hdivider())

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Tab 1: Fix Mistakes
        fix_tab = QWidget()
        fix_layout = QVBoxLayout(fix_tab)
        
        lbl = QLabel("Undo Recent Actions (Hover over an action for details)")
        lbl.setObjectName("H2")
        fix_layout.addWidget(lbl)
        fix_layout.addWidget(muted("Undoing an action will automatically restore the affected inventory quantities."))

        self._history_table = make_table(["Type", "Date", "Summary", "Action"])
        self._history_table.setColumnWidth(0, 100)
        self._history_table.setColumnWidth(1, 150)
        self._history_table.setColumnWidth(3, 100)
        fix_layout.addWidget(self._history_table)
        self._tabs.addTab(fix_tab, "Undo Mistakes")

        # Tab 2: System Settings
        sys_tab = QWidget()
        sys_layout = QVBoxLayout(sys_tab)
        sys_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sys_layout.setSpacing(20)

        sys_layout.addWidget(QLabel("Change Admin Password"))
        pwd_btn = secondary_btn("Update Password")
        pwd_btn.setFixedWidth(200)
        pwd_btn.clicked.connect(self._change_password)
        sys_layout.addWidget(pwd_btn)

        sys_layout.addWidget(hdivider())

        sys_layout.addWidget(QLabel("Danger Zone"))
        sys_layout.addWidget(muted("Warning: This will permanently delete ALL items, recipes, and history."))
        reset_btn = danger_btn("🧨 Factory Reset Database")
        reset_btn.setFixedWidth(250)
        reset_btn.clicked.connect(self._factory_reset)
        sys_layout.addWidget(reset_btn)

        self._tabs.addTab(sys_tab, "System Config")

        return w

    # ── Logic ─────────────────────────────────────────────────────────────────

    def refresh(self):
        # Only refresh if unlocked
        if self._stack.currentWidget() != self._tools_screen:
            return
        
        tbl = self._history_table
        tbl.setRowCount(0)
        row_idx = 0

        # Load recent sales
        sales = db.get_sales_history(days=7, limit=20)
        for s in sales:
            tbl.insertRow(row_idx)
            tbl.setItem(row_idx, 0, centered_item("Sale", SUCCESS))
            tbl.setItem(row_idx, 1, table_item(s['sold_at'][:16].replace('T', ' ')))
            tbl.setItem(row_idx, 2, table_item(f"Sold {s['quantity_sold']}x {s['menu_item_name']}"))
            
            btn = icon_btn("↩ Undo")
            btn.clicked.connect(lambda _, sid=s['id']: self._do_undo('sale', sid))
            tbl.setCellWidget(row_idx, 3, btn)
            tbl.setRowHeight(row_idx, 36)
            row_idx += 1

        # Load recent purchases
        purchases = db.get_purchase_history(limit=20)
        for p in purchases:
            tbl.insertRow(row_idx)
            tbl.setItem(row_idx, 0, centered_item("Purchase", INFO))
            tbl.setItem(row_idx, 1, table_item(p['purchased_at'][:16].replace('T', ' ')))
            tbl.setItem(row_idx, 2, table_item(f"Received {p['quantity']:g} {p['unit_abbr']} of {p['item_name']}"))
            
            btn = icon_btn("↩ Undo")
            btn.clicked.connect(lambda _, pid=p['id']: self._do_undo('purchase', pid))
            tbl.setCellWidget(row_idx, 3, btn)
            tbl.setRowHeight(row_idx, 36)
            row_idx += 1

    def _do_undo(self, log_type, record_id):
        reply = QMessageBox.question(
            self, "Confirm Undo",
            "Are you sure you want to undo this action?\nInventory levels will be adjusted automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if log_type == 'sale':
                    db.undo_sale(record_id)
                elif log_type == 'purchase':
                    db.undo_purchase(record_id)
                self.refresh()
                QMessageBox.information(self, "Success", "Action undone successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not undo action: {e}")

    def _change_password(self):
        new_pass, ok = QInputDialog.getText(self, "Change Password", "Enter new admin password:", QLineEdit.EchoMode.Password)
        if ok and new_pass.strip():
            db.change_admin_password(new_pass.strip())
            QMessageBox.information(self, "Success", "Admin password updated.")

    def _factory_reset(self):
        reply = QMessageBox.critical(
            self, "FACTORY RESET",
            "WARNING!\nThis will wipe all items, recipes, sales, and purchases. You CANNOT undo this.\n\nType 'RESET' to confirm:",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        # Note: QInputDialog is better here to force typing 'RESET'
        text, ok = QInputDialog.getText(self, "Confirm Reset", "Type 'RESET' to wipe the database:")
        if ok and text == 'RESET':
            try:
                db.factory_reset_database()
                QMessageBox.information(self, "Wiped", "System has been factory reset.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))