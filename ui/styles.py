"""
ui/styles.py
Central theme for the Deli Inventory app.
Warm, food-industry palette — clean readability for kitchen staff.
"""

# ── Color Palette ─────────────────────────────────────────────────────────────
DARK_BG       = "#1C1C1E"      # main window background
PANEL_BG      = "#2C2C2E"      # card / panel surface
SIDEBAR_BG    = "#111113"      # left nav
BORDER        = "#3A3A3C"

ACCENT        = "#E8956D"      # warm terracotta — primary action
ACCENT_HOVER  = "#F0A882"
ACCENT_DARK   = "#C4714A"

SUCCESS       = "#4CAF50"
WARNING       = "#FFC107"
DANGER        = "#F44336"
INFO          = "#64B5F6"

TEXT_PRIMARY  = "#F2F2F7"
TEXT_SECOND   = "#AEAEB2"
TEXT_MUTED    = "#636366"

NAV_ACTIVE    = ACCENT
NAV_HOVER     = "#3A3A3C"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY   = "Segoe UI"
FONT_MONO     = "Consolas"
FONT_SIZE_SM  = 9
FONT_SIZE_MD  = 10
FONT_SIZE_LG  = 12
FONT_SIZE_XL  = 16
FONT_SIZE_H1  = 22

# ── Dimensions ────────────────────────────────────────────────────────────────
SIDEBAR_W     = 200
WINDOW_W      = 1280
WINDOW_H      = 820
CORNER_RADIUS = 8
PADDING       = 16

# ── Full QSS Stylesheet ───────────────────────────────────────────────────────
STYLESHEET = f"""
/* ── Global ──────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE_MD}pt;
}}

QMainWindow, QDialog {{
    background-color: {DARK_BG};
}}

/* ── Scroll bars ─────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 8px; background: {PANEL_BG}; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 4px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
#Sidebar {{
    background-color: {SIDEBAR_BG};
    border-right: 1px solid {BORDER};
}}

/* ── Nav Buttons ─────────────────────────────────────────────────────── */
QPushButton#NavBtn {{
    background: transparent;
    color: {TEXT_SECOND};
    border: none;
    text-align: left;
    padding: 10px 16px;
    font-size: {FONT_SIZE_MD}pt;
    border-radius: 6px;
    margin: 1px 8px;
}}
QPushButton#NavBtn:hover {{
    background-color: {NAV_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton#NavBtn[active="true"] {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
}}

/* ── Primary Button ──────────────────────────────────────────────────── */
QPushButton#PrimaryBtn {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: {FONT_SIZE_MD}pt;
    font-weight: 600;
}}
QPushButton#PrimaryBtn:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#PrimaryBtn:pressed {{ background-color: {ACCENT_DARK}; }}
QPushButton#PrimaryBtn:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}

/* ── Secondary Button ────────────────────────────────────────────────── */
QPushButton#SecondaryBtn {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: {FONT_SIZE_MD}pt;
}}
QPushButton#SecondaryBtn:hover {{ background-color: {NAV_HOVER}; }}

/* ── Danger Button ───────────────────────────────────────────────────── */
QPushButton#DangerBtn {{
    background-color: {DANGER};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: {FONT_SIZE_MD}pt;
    font-weight: 600;
}}
QPushButton#DangerBtn:hover {{ background-color: #E53935; }}

/* ── Icon Button (small square) ──────────────────────────────────────── */
QPushButton#IconBtn {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 4px 8px;
    color: {TEXT_SECOND};
    font-size: {FONT_SIZE_SM}pt;
}}
QPushButton#IconBtn:hover {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
}}

/* ── Cards / Panels ──────────────────────────────────────────────────── */
QFrame#Card {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: {CORNER_RADIUS}px;
    padding: {PADDING}px;
}}
QFrame#StatsCard {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: {CORNER_RADIUS}px;
}}

/* ── Table ───────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: {CORNER_RADIUS}px;
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: rgba(232,149,109,0.25);
    color: {TEXT_PRIMARY};
}}
QHeaderView::section {{
    background-color: {DARK_BG};
    color: {TEXT_SECOND};
    font-size: {FONT_SIZE_SM}pt;
    font-weight: 600;
    text-transform: uppercase;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {BORDER};
}}

/* ── Form Inputs ─────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {DARK_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_MD}pt;
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox {{
    background-color: {DARK_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_MD}pt;
    min-width: 120px;
}}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    outline: none;
}}
QDoubleSpinBox, QSpinBox {{
    background-color: {DARK_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_MD}pt;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    background: {PANEL_BG};
    border: none;
    width: 20px;
}}
QDateEdit {{
    background-color: {DARK_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {TEXT_PRIMARY};
}}
QDateEdit:focus {{ border-color: {ACCENT}; }}
QDateEdit::drop-down {{ border: none; }}
QCalendarWidget {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
}}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel#H1 {{
    font-size: {FONT_SIZE_H1}pt;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
QLabel#H2 {{
    font-size: {FONT_SIZE_XL}pt;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}
QLabel#Muted {{
    color: {TEXT_MUTED};
    font-size: {FONT_SIZE_SM}pt;
}}
QLabel#StatValue {{
    font-size: 26pt;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
QLabel#StatLabel {{
    font-size: {FONT_SIZE_SM}pt;
    color: {TEXT_SECOND};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#Badge {{
    border-radius: 10px;
    padding: 2px 8px;
    font-size: {FONT_SIZE_SM}pt;
    font-weight: 600;
}}
QLabel#LowStock {{
    background-color: rgba(244,67,54,0.20);
    color: {DANGER};
    border-radius: 4px;
    padding: 2px 7px;
    font-size: {FONT_SIZE_SM}pt;
    font-weight: 600;
}}
QLabel#OkStock {{
    background-color: rgba(76,175,80,0.18);
    color: {SUCCESS};
    border-radius: 4px;
    padding: 2px 7px;
    font-size: {FONT_SIZE_SM}pt;
    font-weight: 600;
}}
QLabel#WarnStock {{
    background-color: rgba(255,193,7,0.18);
    color: {WARNING};
    border-radius: 4px;
    padding: 2px 7px;
    font-size: {FONT_SIZE_SM}pt;
    font-weight: 600;
}}
QLabel#SectionTitle {{
    font-size: {FONT_SIZE_LG}pt;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    padding-bottom: 4px;
}}
QLabel#AppName {{
    font-size: 15pt;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    padding: 4px 0;
}}
QLabel#AppSub {{
    font-size: {FONT_SIZE_SM}pt;
    color: {TEXT_MUTED};
}}

/* ── Tab Widget ──────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {CORNER_RADIUS}px;
    background: {PANEL_BG};
}}
QTabBar::tab {{
    background: {DARK_BG};
    color: {TEXT_SECOND};
    padding: 8px 18px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {PANEL_BG};
    color: {ACCENT};
    font-weight: 600;
}}

/* ── Message Box ─────────────────────────────────────────────────────── */
QMessageBox {{
    background-color: {PANEL_BG};
}}
QMessageBox QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    min-width: 70px;
}}
QMessageBox QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}

/* ── Tooltip ─────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* ── Separator ───────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ── Status Bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {SIDEBAR_BG};
    color: {TEXT_MUTED};
    font-size: {FONT_SIZE_SM}pt;
    border-top: 1px solid {BORDER};
}}

/* ── Group Box ───────────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    color: {TEXT_SECOND};
    font-size: {FONT_SIZE_SM}pt;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    color: {TEXT_SECOND};
}}

/* ── Check Box ───────────────────────────────────────────────────────── */
QCheckBox {{ color: {TEXT_PRIMARY}; spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {DARK_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
"""
