"""
db/database.py  –  Simplified Deli Inventory
Only tracks: items, categories, units, purchases, and stock counts.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "deli_inventory.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialize_database():
    conn = get_connection()
    conn.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS units (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL UNIQUE,
            abbreviation TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS items (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL UNIQUE,
            category_id      INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            unit_id          INTEGER NOT NULL REFERENCES units(id),
            current_quantity REAL NOT NULL DEFAULT 0,
            min_threshold    REAL NOT NULL DEFAULT 0,
            supplier         TEXT,
            notes            TEXT,
            is_active        INTEGER NOT NULL DEFAULT 1,
            updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id        INTEGER NOT NULL REFERENCES items(id),
            quantity       REAL NOT NULL,
            unit_cost      REAL NOT NULL DEFAULT 0,
            invoice_number TEXT,
            supplier       TEXT,
            received_by    TEXT,
            notes          TEXT,
            purchased_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS stock_counts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER NOT NULL REFERENCES items(id),
            quantity    REAL NOT NULL,
            counted_by  TEXT,
            counted_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        INSERT OR IGNORE INTO categories (name) VALUES
            ('Deli Meats'), ('Cheese'), ('Produce'), ('Bread'),
            ('Dairy'), ('Ice Cream'), ('Dry Goods'), ('Condiments'),
            ('Beverages'), ('Packaging');

        INSERT OR IGNORE INTO units (name, abbreviation) VALUES
            ('pounds',       'lbs'),
            ('ounces',       'oz'),
            ('kilograms',    'kg'),
            ('grams',        'g'),
            ('gallons',      'gal'),
            ('quarts',       'qt'),
            ('pints',        'pt'),
            ('fluid ounces', 'fl oz'),
            ('liters',       'L'),
            ('count',        'ct'),
            ('cases',        'case'),
            ('loaves',       'loaf'),
            ('slices',       'sl'),
            ('bags',         'bag'),
            ('jars',         'jar'),
            ('bottles',      'btl');

        INSERT OR IGNORE INTO app_settings (key, value)
            VALUES ('admin_pass', 'admin123');
    """)
    conn.commit()
    conn.close()


# ── Categories & Units ────────────────────────────────────────────────────────

def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_units():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM units ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Items ─────────────────────────────────────────────────────────────────────

def get_all_items(include_inactive=False):
    conn = get_connection()
    where = "" if include_inactive else "WHERE i.is_active = 1"
    rows = conn.execute(f"""
        SELECT i.*, c.name AS category_name,
               u.abbreviation AS unit_abbr, u.name AS unit_name
        FROM   items i
        LEFT JOIN categories c ON i.category_id = c.id
        JOIN  units u           ON i.unit_id     = u.id
        {where}
        ORDER BY i.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_item(name, category_id, unit_id, current_quantity=0,
             min_threshold=0, supplier=None, notes=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO items (name, category_id, unit_id, current_quantity,
                           min_threshold, supplier, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, category_id, unit_id, current_quantity,
          min_threshold, supplier, notes))
    conn.commit()
    conn.close()


def update_item(item_id, **kwargs):
    allowed = {'name', 'category_id', 'unit_id', 'min_threshold',
               'supplier', 'notes', 'is_active'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields['updated_at'] = datetime.now().isoformat(sep=' ', timespec='seconds')
    sets   = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    conn   = get_connection()
    conn.execute(f"UPDATE items SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_low_stock_items():
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, c.name AS category_name, u.abbreviation AS unit_abbr
        FROM   items i
        LEFT JOIN categories c ON i.category_id = c.id
        JOIN  units u           ON i.unit_id = u.id
        WHERE  i.is_active = 1 AND i.current_quantity <= i.min_threshold
        ORDER  BY (i.current_quantity / MAX(i.min_threshold, 0.001)) ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Purchases ─────────────────────────────────────────────────────────────────

def log_purchase(item_id, quantity, unit_cost=0, invoice_number=None,
                 supplier=None, received_by=None, notes=None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO purchases
                (item_id, quantity, unit_cost, invoice_number, supplier, received_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, quantity, unit_cost, invoice_number, supplier, received_by, notes))
        conn.execute("""
            UPDATE items
            SET current_quantity = current_quantity + ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (quantity, item_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_purchase_history(limit=500):
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, i.name AS item_name, u.abbreviation AS unit_abbr
        FROM   purchases p
        JOIN   items i ON p.item_id = i.id
        JOIN   units u ON i.unit_id = u.id
        ORDER  BY p.purchased_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def undo_purchase(purchase_id: int):
    conn = get_connection()
    p = conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
    if p:
        conn.execute("""
            UPDATE items SET current_quantity = MAX(0, current_quantity - ?),
                             updated_at = datetime('now')
            WHERE id = ?
        """, (p['quantity'], p['item_id']))
        conn.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        conn.commit()
    conn.close()


# ── Stock Counts ──────────────────────────────────────────────────────────────

def save_stock_count(counts: list[dict], counted_by: str = None):
    """
    counts: list of {item_id, quantity}
    Sets each item's current_quantity to the counted value and logs it.
    """
    conn = get_connection()
    try:
        for entry in counts:
            conn.execute("""
                UPDATE items
                SET current_quantity = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (entry['quantity'], entry['item_id']))
            conn.execute("""
                INSERT INTO stock_counts (item_id, quantity, counted_by)
                VALUES (?, ?, ?)
            """, (entry['item_id'], entry['quantity'], counted_by))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_stock_count_history(limit=200):
    conn = get_connection()
    rows = conn.execute("""
        SELECT sc.*, i.name AS item_name, u.abbreviation AS unit_abbr
        FROM   stock_counts sc
        JOIN   items i ON sc.item_id = i.id
        JOIN   units u ON i.unit_id  = u.id
        ORDER  BY sc.counted_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Admin ─────────────────────────────────────────────────────────────────────

def verify_admin(password: str) -> bool:
    conn = get_connection()
    row  = conn.execute("SELECT value FROM app_settings WHERE key='admin_pass'").fetchone()
    conn.close()
    return row and row['value'] == password


def change_admin_password(new_pass: str):
    conn = get_connection()
    conn.execute("UPDATE app_settings SET value=? WHERE key='admin_pass'", (new_pass,))
    conn.commit()
    conn.close()


def factory_reset_database():
    conn = get_connection()
    for t in ['purchases', 'stock_counts', 'items']:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
