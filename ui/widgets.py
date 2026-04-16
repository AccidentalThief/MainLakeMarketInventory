"""
ui/widgets.py
Reusable widget helpers for consistent UI across all panels.
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFrame, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
from ui.styles import (
    TEXT_PRIMARY, TEXT_SECOND, ACCENT, SUCCESS, WARNING,
    DANGER, PANEL_BG, BORDER, TEXT_MUTED
)


# ── Button factory ────────────────────────────────────────────────────────────

def primary_btn(text: str, icon: str = "") -> QPushButton:
    btn = QPushButton(f"{icon}  {text}".strip() if icon else text)
    btn.setObjectName("PrimaryBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def secondary_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("SecondaryBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def danger_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("DangerBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def icon_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("IconBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# ── Label factory ─────────────────────────────────────────────────────────────

def h1(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("H1")
    return lbl


def h2(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("H2")
    return lbl


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("SectionTitle")
    return lbl


def muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("Muted")
    return lbl


def stock_badge(qty: float, threshold: float, unit: str) -> QLabel:
    """Returns a colored badge label for stock status."""
    text = f"{qty:g} {unit}"
    lbl  = QLabel(text)
    if qty <= threshold:
        lbl.setObjectName("LowStock")
    elif qty <= threshold * 1.5:
        lbl.setObjectName("WarnStock")
    else:
        lbl.setObjectName("OkStock")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def status_badge(text: str, color: str) -> QLabel:
    """Generic colored pill badge."""
    lbl = QLabel(text)
    lbl.setObjectName("Badge")
    lbl.setStyleSheet(
        f"background-color: {color}33; color: {color}; "
        f"border-radius: 10px; padding: 2px 8px; "
        f"font-size: 9pt; font-weight: 600;"
    )
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


# ── Divider ───────────────────────────────────────────────────────────────────

def hdivider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


# ── Stat card ─────────────────────────────────────────────────────────────────

def stat_card(label: str, value: str, accent_color: str = ACCENT,
              subtitle: str = "") -> QFrame:
    card = QFrame()
    card.setObjectName("StatsCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(2)

    top = QHBoxLayout()
    lbl = QLabel(label.upper())
    lbl.setObjectName("StatLabel")
    top.addWidget(lbl)
    top.addStretch()
    layout.addLayout(top)

    val = QLabel(value)
    val.setObjectName("StatValue")
    val.setStyleSheet(f"color: {accent_color}; font-size: 26pt; font-weight: 700;")
    layout.addWidget(val)

    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName("Muted")
        layout.addWidget(sub)

    return card


# ── Search bar ────────────────────────────────────────────────────────────────

def search_bar(placeholder: str = "Search…") -> QLineEdit:
    edit = QLineEdit()
    edit.setPlaceholderText(f"🔍  {placeholder}")
    edit.setObjectName("SearchBar")
    edit.setStyleSheet("""
        QLineEdit {
            background-color: #2C2C2E;
            border: 1px solid #3A3A3C;
            border-radius: 20px;
            padding: 7px 14px;
            font-size: 10pt;
        }
        QLineEdit:focus { border-color: #E8956D; }
    """)
    return edit


# ── Standard table ────────────────────────────────────────────────────────────

def make_table(columns: list[str]) -> QTableWidget:
    tbl = QTableWidget()
    tbl.setColumnCount(len(columns))
    tbl.setHorizontalHeaderLabels(columns)
    tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tbl.setAlternatingRowColors(False)
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(True)
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return tbl


def table_item(text: str, align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
               color: str = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(align)
    if color:
        item.setForeground(QColor(color))
    return item


def centered_item(text: str, color: str = None) -> QTableWidgetItem:
    return table_item(text,
                      Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                      color)


# ── Empty state ───────────────────────────────────────────────────────────────

def empty_state(icon: str, message: str, sub: str = "") -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(8)

    ico = QLabel(icon)
    ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ico.setStyleSheet("font-size: 36pt;")
    layout.addWidget(ico)

    msg = QLabel(message)
    msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
    msg.setStyleSheet(f"font-size: 13pt; font-weight: 600; color: {TEXT_SECOND};")
    layout.addWidget(msg)

    if sub:
        s = QLabel(sub)
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setStyleSheet(f"font-size: 10pt; color: {TEXT_MUTED};")
        layout.addWidget(s)

    return w


# ── Section header row ────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", actions: list = None) -> QWidget:
    w = QWidget()
    
    # Force the header to stay compact vertically
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    t = h1(title)
    text_col.addWidget(t)
    if subtitle:
        s = muted(subtitle)
        text_col.addWidget(s)
    row.addLayout(text_col)
    row.addStretch()

    if actions:
        for btn in actions:
            row.addWidget(btn)

    return w
