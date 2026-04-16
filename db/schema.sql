-- ============================================================
--  Deli & Ice Cream Parlor Inventory Management
--  SQLite Schema  |  Designed for easy migration to PostgreSQL
-- ============================================================
-- Notes for PostgreSQL migration:
--   • Replace INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
--   • Replace TEXT → VARCHAR / TEXT (already compatible)
--   • Add created_at DEFAULT now() (already compatible via CURRENT_TIMESTAMP)
--   • Wrap in a schema namespace (e.g. CREATE SCHEMA inventory;)
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ------------------------------------------------------------
-- CATEGORIES  (Deli, Ice Cream, Dry Goods, Produce, etc.)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    color_hex   TEXT    DEFAULT '#607D8B',   -- UI badge color
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- UNITS OF MEASUREMENT
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS units (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL UNIQUE,   -- e.g. "lbs", "oz", "gallon", "count"
    abbreviation TEXT    NOT NULL,
    unit_type    TEXT    NOT NULL CHECK(unit_type IN ('weight','volume','count','other'))
);

-- ------------------------------------------------------------
-- INVENTORY ITEMS  (ingredients + packaged goods)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    category_id         INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    unit_id             INTEGER NOT NULL REFERENCES units(id),
    current_quantity    REAL    NOT NULL DEFAULT 0,
    min_threshold       REAL    NOT NULL DEFAULT 0,   -- low-stock warning trigger
    reorder_quantity    REAL,                          -- suggested order qty
    par_level           REAL,                          -- ideal stock level
    supplier            TEXT,
    notes               TEXT,
    is_active           INTEGER NOT NULL DEFAULT 1,    -- soft delete
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- ITEM EXPIRATION TRACKING
-- Each lot/batch of an item can have its own expiration date
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS item_expiration_lots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    quantity        REAL    NOT NULL,
    expiration_date TEXT,                              -- ISO date YYYY-MM-DD
    received_date   TEXT    NOT NULL DEFAULT (date('now')),
    notes           TEXT,
    is_depleted     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- PURCHASE / RECEIVING LOG  (incoming orders, COGS tracking)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         INTEGER NOT NULL REFERENCES items(id),
    quantity        REAL    NOT NULL,
    unit_cost       REAL    NOT NULL DEFAULT 0,        -- cost per unit
    total_cost      REAL    GENERATED ALWAYS AS (quantity * unit_cost) STORED,
    invoice_number  TEXT,
    supplier        TEXT,
    received_by     TEXT,
    notes           TEXT,
    purchased_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- SANDWICH / MENU ITEM RECIPES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    category    TEXT    DEFAULT 'Sandwich',   -- Sandwich, Ice Cream, etc.
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_item_id    INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    item_id         INTEGER NOT NULL REFERENCES items(id),
    quantity        REAL    NOT NULL,          -- amount used per 1 menu item sold
    UNIQUE(menu_item_id, item_id)
);

-- ------------------------------------------------------------
-- SALES / USAGE LOG  (logs sandwich sales → auto-deducts inventory)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_item_id    INTEGER REFERENCES menu_items(id),
    quantity_sold   INTEGER NOT NULL DEFAULT 1,
    logged_by       TEXT,
    notes           TEXT,
    sold_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- MANUAL USAGE LOG  (ad-hoc ingredient usage not tied to a recipe)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES items(id),
    quantity    REAL    NOT NULL,
    reason      TEXT,                          -- "prep", "tasting", "spill", etc.
    logged_by   TEXT,
    used_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- WASTE LOG  (expired, spoiled, discarded inventory)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waste_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         INTEGER NOT NULL REFERENCES items(id),
    quantity        REAL    NOT NULL,
    reason          TEXT    NOT NULL CHECK(reason IN (
                        'expired','spoiled','dropped','overproduction',
                        'quality_issue','other'
                    )),
    estimated_cost  REAL,                      -- COGS value of wasted goods
    logged_by       TEXT,
    notes           TEXT,
    wasted_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
--  SEED DATA
-- ============================================================

-- Default categories
INSERT OR IGNORE INTO categories (name, color_hex) VALUES
    ('Deli Meats',    '#C0392B'),
    ('Cheese',        '#E67E22'),
    ('Produce',       '#27AE60'),
    ('Bread',         '#D4A017'),
    ('Dairy',         '#2980B9'),
    ('Ice Cream',     '#8E44AD'),
    ('Dry Goods',     '#7F8C8D'),
    ('Condiments',    '#16A085'),
    ('Beverages',     '#2C3E50'),
    ('Packaging',     '#95A5A6');

-- Default units
INSERT OR IGNORE INTO units (name, abbreviation, unit_type) VALUES
    ('pounds',      'lbs',   'weight'),
    ('ounces',      'oz',    'weight'),
    ('kilograms',   'kg',    'weight'),
    ('grams',       'g',     'weight'),
    ('gallons',     'gal',   'volume'),
    ('quarts',      'qt',    'volume'),
    ('pints',       'pt',    'volume'),
    ('fluid ounces','fl oz', 'volume'),
    ('liters',      'L',     'volume'),
    ('count',       'ct',    'count'),
    ('cases',       'case',  'count'),
    ('loaves',      'loaf',  'count'),
    ('slices',      'sl',    'count'),
    ('bags',        'bag',   'count'),
    ('jars',        'jar',   'count'),
    ('bottles',     'btl',   'count');
