"""
db/database.py
Central database access layer for Deli Inventory Management.
Uses SQLite now; structured for easy swap to PostgreSQL later.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime, date

# ── Path resolution ───────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
DB_PATH    = BASE_DIR / "deli_inventory.db"
SCHEMA_SQL = Path(__file__).resolve().parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Return a connection with row_factory set to Row for dict-like access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialize_database():
    """Create tables and seed data if the database doesn't exist yet."""
    conn = get_connection()
    with open(SCHEMA_SQL, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  UNITS
# ═══════════════════════════════════════════════════════════════════════════════

def get_units():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM units ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  ITEMS
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_items(include_inactive=False):
    conn = get_connection()
    sql = """
        SELECT i.*, c.name AS category_name, c.color_hex,
               u.abbreviation AS unit_abbr, u.name AS unit_name
        FROM   items i
        LEFT   JOIN categories c ON i.category_id = c.id
        JOIN   units u            ON i.unit_id     = u.id
        {}
        ORDER  BY i.name
    """.format("" if include_inactive else "WHERE i.is_active = 1")
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_item(item_id: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT i.*, c.name AS category_name, u.abbreviation AS unit_abbr
        FROM   items i
        LEFT   JOIN categories c ON i.category_id = c.id
        JOIN   units u            ON i.unit_id     = u.id
        WHERE  i.id = ?
    """, (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_low_stock_items():
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, c.name AS category_name, c.color_hex,
               u.abbreviation AS unit_abbr
        FROM   items i
        LEFT   JOIN categories c ON i.category_id = c.id
        JOIN   units u            ON i.unit_id     = u.id
        WHERE  i.is_active = 1
          AND  i.current_quantity <= i.min_threshold
        ORDER  BY (i.current_quantity / MAX(i.min_threshold, 0.001)) ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_item(name, category_id, unit_id, current_quantity=0, min_threshold=0,
             reorder_quantity=None, par_level=None, supplier=None, notes=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO items (name, category_id, unit_id, current_quantity, min_threshold,
                           reorder_quantity, par_level, supplier, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category_id, unit_id, current_quantity, min_threshold,
          reorder_quantity, par_level, supplier, notes))
    conn.commit()
    conn.close()


def update_item(item_id, **kwargs):
    allowed = {'name','category_id','unit_id','min_threshold',
               'reorder_quantity','par_level','supplier','notes','is_active'}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields['updated_at'] = datetime.now().isoformat(sep=' ', timespec='seconds')
    sets   = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    conn   = get_connection()
    conn.execute(f"UPDATE items SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def adjust_item_quantity(conn, item_id: int, delta: float):
    """Add delta (positive or negative) to current_quantity. Call within an open conn."""
    conn.execute("""
        UPDATE items
        SET    current_quantity = MAX(0, current_quantity + ?),
               updated_at       = datetime('now')
        WHERE  id = ?
    """, (delta, item_id))


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPIRATION LOTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_expiring_soon(days_ahead=7):
    conn = get_connection()
    rows = conn.execute("""
        SELECT l.*, i.name AS item_name, u.abbreviation AS unit_abbr
        FROM   item_expiration_lots l
        JOIN   items i ON l.item_id = i.id
        JOIN   units u ON i.unit_id = u.id
        WHERE  l.is_depleted = 0
          AND  l.expiration_date IS NOT NULL
          AND  date(l.expiration_date) <= date('now', ? || ' days')
        ORDER  BY l.expiration_date ASC
    """, (str(days_ahead),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_expiration_lot(item_id, quantity, expiration_date=None, notes=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO item_expiration_lots (item_id, quantity, expiration_date, notes)
        VALUES (?, ?, ?, ?)
    """, (item_id, quantity, expiration_date, notes))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  PURCHASES
# ═══════════════════════════════════════════════════════════════════════════════

def log_purchase(item_id, quantity, unit_cost, invoice_number=None,
                 supplier=None, received_by=None, notes=None,
                 expiration_date=None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO purchases (item_id, quantity, unit_cost,
                                   invoice_number, supplier, received_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, quantity, unit_cost, invoice_number,
              supplier, received_by, notes))
        adjust_item_quantity(conn, item_id, quantity)
        if expiration_date:
            conn.execute("""
                INSERT INTO item_expiration_lots (item_id, quantity, expiration_date)
                VALUES (?, ?, ?)
            """, (item_id, quantity, expiration_date))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_purchase_history(item_id=None, limit=200):
    conn = get_connection()
    if item_id:
        rows = conn.execute("""
            SELECT p.*, i.name AS item_name, u.abbreviation AS unit_abbr
            FROM   purchases p
            JOIN   items i ON p.item_id = i.id
            JOIN   units u ON i.unit_id = u.id
            WHERE  p.item_id = ?
            ORDER  BY p.purchased_at DESC LIMIT ?
        """, (item_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.*, i.name AS item_name, u.abbreviation AS unit_abbr
            FROM   purchases p
            JOIN   items i ON p.item_id = i.id
            JOIN   units u ON i.unit_id = u.id
            ORDER  BY p.purchased_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_purchase_summary(days=30):
    """Total COGS grouped by item for the last N days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.name AS item_name, u.abbreviation AS unit_abbr,
               SUM(p.quantity)   AS total_qty,
               SUM(p.total_cost) AS total_cost
        FROM   purchases p
        JOIN   items i ON p.item_id = i.id
        JOIN   units u ON i.unit_id = u.id
        WHERE  p.purchased_at >= datetime('now', ? || ' days')
        GROUP  BY p.item_id
        ORDER  BY total_cost DESC
    """, (f"-{days}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  MENU ITEMS & RECIPES
# ═══════════════════════════════════════════════════════════════════════════════

def get_menu_items(active_only=True):
    conn = get_connection()
    sql = "SELECT * FROM menu_items"
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY category, name"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recipe(menu_item_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ri.*, i.name AS ingredient_name, u.abbreviation AS unit_abbr
        FROM   recipe_ingredients ri
        JOIN   items i ON ri.item_id = i.id
        JOIN   units u ON i.unit_id  = u.id
        WHERE  ri.menu_item_id = ?
    """, (menu_item_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_menu_item(name, category="Sandwich", description=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO menu_items (name, category, description) VALUES (?, ?, ?)",
        (name, category, description)
    )
    conn.commit()
    conn.close()


def save_recipe(menu_item_id: int, ingredients: list[dict]):
    """ingredients: list of {item_id, quantity}"""
    conn = get_connection()
    conn.execute("DELETE FROM recipe_ingredients WHERE menu_item_id = ?", (menu_item_id,))
    for ing in ingredients:
        conn.execute("""
            INSERT INTO recipe_ingredients (menu_item_id, item_id, quantity)
            VALUES (?, ?, ?)
        """, (menu_item_id, ing['item_id'], ing['quantity']))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  SALES LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log_sale(menu_item_id: int, quantity_sold: int = 1,
             logged_by: str = None, notes: str = None):
    """Record a sale and deduct ingredients from inventory."""
    recipe = get_recipe(menu_item_id)
    if not recipe:
        raise ValueError("No recipe found for this menu item.")
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sales_log (menu_item_id, quantity_sold, logged_by, notes)
            VALUES (?, ?, ?, ?)
        """, (menu_item_id, quantity_sold, logged_by, notes))
        for ing in recipe:
            adjust_item_quantity(conn, ing['item_id'],
                                 -(ing['quantity'] * quantity_sold))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sales_history(days=30, limit=500):
    conn = get_connection()
    rows = conn.execute("""
        SELECT sl.*, m.name AS menu_item_name, m.category
        FROM   sales_log sl
        JOIN   menu_items m ON sl.menu_item_id = m.id
        WHERE  sl.sold_at >= datetime('now', ? || ' days')
        ORDER  BY sl.sold_at DESC LIMIT ?
    """, (f"-{days}", limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  MANUAL USAGE LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log_usage(item_id: int, quantity: float, reason: str = None,
              logged_by: str = None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO usage_log (item_id, quantity, reason, logged_by)
            VALUES (?, ?, ?, ?)
        """, (item_id, quantity, reason, logged_by))
        adjust_item_quantity(conn, item_id, -quantity)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_usage_history(days=30):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ul.*, i.name AS item_name, u.abbreviation AS unit_abbr
        FROM   usage_log ul
        JOIN   items i ON ul.item_id = i.id
        JOIN   units u ON i.unit_id  = u.id
        WHERE  ul.used_at >= datetime('now', ? || ' days')
        ORDER  BY ul.used_at DESC
    """, (f"-{days}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  WASTE LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log_waste(item_id: int, quantity: float, reason: str,
              estimated_cost: float = None,
              logged_by: str = None, notes: str = None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO waste_log (item_id, quantity, reason,
                                   estimated_cost, logged_by, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item_id, quantity, reason, estimated_cost, logged_by, notes))
        adjust_item_quantity(conn, item_id, -quantity)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_waste_history(days=30):
    conn = get_connection()
    rows = conn.execute("""
        SELECT wl.*, i.name AS item_name, u.abbreviation AS unit_abbr
        FROM   waste_log wl
        JOIN   items i ON wl.item_id = i.id
        JOIN   units u ON i.unit_id  = u.id
        WHERE  wl.wasted_at >= datetime('now', ? || ' days')
        ORDER  BY wl.wasted_at DESC
    """, (f"-{days}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_waste_summary(days=30):
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.name AS item_name, u.abbreviation AS unit_abbr,
               wl.reason,
               SUM(wl.quantity)       AS total_qty,
               SUM(wl.estimated_cost) AS total_cost
        FROM   waste_log wl
        JOIN   items i ON wl.item_id = i.id
        JOIN   units u ON i.unit_id  = u.id
        WHERE  wl.wasted_at >= datetime('now', ? || ' days')
        GROUP  BY wl.item_id, wl.reason
        ORDER  BY total_cost DESC NULLS LAST
    """, (f"-{days}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════════════════

def get_dashboard_stats():
    conn = get_connection()
    stats = {}

    stats['total_items'] = conn.execute(
        "SELECT COUNT(*) FROM items WHERE is_active=1").fetchone()[0]
    stats['low_stock_count'] = conn.execute(
        "SELECT COUNT(*) FROM items WHERE is_active=1 AND current_quantity<=min_threshold"
    ).fetchone()[0]
    stats['expiring_soon'] = conn.execute("""
        SELECT COUNT(*) FROM item_expiration_lots
        WHERE  is_depleted=0 AND expiration_date IS NOT NULL
          AND  date(expiration_date) <= date('now','+7 days')
    """).fetchone()[0]
    stats['cogs_30d'] = conn.execute("""
        SELECT COALESCE(SUM(total_cost),0) FROM purchases
        WHERE  purchased_at >= datetime('now','-30 days')
    """).fetchone()[0]
    stats['waste_cost_30d'] = conn.execute("""
        SELECT COALESCE(SUM(estimated_cost),0) FROM waste_log
        WHERE  wasted_at >= datetime('now','-30 days')
    """).fetchone()[0]
    stats['sales_today'] = conn.execute("""
        SELECT COALESCE(SUM(quantity_sold),0) FROM sales_log
        WHERE  date(sold_at) = date('now')
    """).fetchone()[0]

    conn.close()
    return stats

# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN & SYSTEM CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

def verify_admin(password: str) -> bool:
    """Creates a settings table if missing, and verifies the admin password."""
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('admin_pass', 'admin123')")
    conn.commit()
    row = conn.execute("SELECT value FROM app_settings WHERE key = 'admin_pass'").fetchone()
    conn.close()
    return row['value'] == password

def change_admin_password(new_pass: str):
    conn = get_connection()
    conn.execute("UPDATE app_settings SET value = ? WHERE key = 'admin_pass'", (new_pass,))
    conn.commit()
    conn.close()

def undo_purchase(purchase_id: int):
    """Deletes a purchase log and removes the items from inventory."""
    conn = get_connection()
    p = conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
    if p:
        adjust_item_quantity(conn, p['item_id'], -p['quantity'])
        conn.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        conn.commit()
    conn.close()

def undo_sale(sale_id: int):
    """Deletes a sale log and adds the recipe ingredients back to inventory."""
    conn = get_connection()
    s = conn.execute("SELECT * FROM sales_log WHERE id = ?", (sale_id,)).fetchone()
    if s:
        recipe = conn.execute("SELECT * FROM recipe_ingredients WHERE menu_item_id = ?", (s['menu_item_id'],)).fetchall()
        for ing in recipe:
            adjust_item_quantity(conn, ing['item_id'], (ing['quantity'] * s['quantity_sold']))
        conn.execute("DELETE FROM sales_log WHERE id = ?", (sale_id,))
        conn.commit()
    conn.close()

def undo_waste(waste_id: int):
    """Deletes a waste log and adds the items back to inventory."""
    conn = get_connection()
    w = conn.execute("SELECT * FROM waste_log WHERE id = ?", (waste_id,)).fetchone()
    if w:
        adjust_item_quantity(conn, w['item_id'], w['quantity'])
        conn.execute("DELETE FROM waste_log WHERE id = ?", (waste_id,))
        conn.commit()
    conn.close()

def factory_reset_database():
    """WIPES ALL DATA. Resets everything except base categories and units."""
    conn = get_connection()
    tables = [
        'purchases', 'sales_log', 'usage_log', 'waste_log', 
        'item_expiration_lots', 'recipe_ingredients', 'menu_items', 'items'
    ]
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
