# 🥪 DeliTrack — Inventory Management System

A desktop inventory management app for deli and ice cream parlors. Runs locally on Windows with SQLite — no internet connection required.

---

## Quick Start (Windows)

### Step 1 — Install Python
Download Python 3.11+ from https://python.org/downloads  
✅ Check **"Add Python to PATH"** during installation.

### Step 2 — Install dependencies
Open a Command Prompt in this folder, then run:
```
pip install -r requirements.txt
```

### Step 3 — Launch the app
```
python main.py
```

The database (`deli_inventory.db`) is created automatically in this folder on first run.

---

## Optional: Create a Desktop Shortcut
To make a double-clickable launcher, run:
```
python build_shortcut.py
```
This creates `DeliTrack.bat` which staff can double-click.

---

## Optional: Build a Standalone .exe (no Python needed)
```
pip install pyinstaller
pyinstaller --onefile --windowed --name DeliTrack main.py
```
The `.exe` will be in the `dist/` folder.

---

## Project Structure

```
deli_inventory/
├── main.py                  ← App entry point
├── requirements.txt
├── deli_inventory.db        ← Auto-created SQLite database
├── db/
│   ├── schema.sql           ← Full database schema
│   └── database.py          ← All DB queries
└── ui/
    ├── styles.py            ← Theme / QSS stylesheet
    ├── widgets.py           ← Reusable UI components
    └── panels/
        ├── dashboard.py     ← Home screen with stats
        ├── inventory.py     ← Item management
        ├── purchases.py     ← Log incoming orders
        ├── sales.py         ← Log sales + recipe manager
        ├── waste.py         ← Waste tracking
        └── history.py       ← Full activity log
```

---

## Migrating to PostgreSQL (future)

The database layer is designed for this. Steps:
1. Replace `sqlite3` with `psycopg2` in `db/database.py`
2. Update `get_connection()` to use a connection string
3. In `schema.sql`: replace `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
4. Export SQLite data with `sqlite3 deli_inventory.db .dump` and import into Postgres

---

## Features

| Feature | Description |
|---|---|
| 📦 Inventory | Track all items with configurable units and par levels |
| ⚠️ Low Stock Alerts | Color-coded warnings when stock hits minimums |
| 🛒 Purchase Log | Log incoming orders, track COGS per item |
| 🥪 Recipe Engine | Configure sandwich ingredients, auto-deduct on sale |
| 🗑 Waste Log | Track spoilage with cost estimates |
| 📋 History | Unified view of all activity by date range |
| 🕒 Expiration Tracking | Flag items expiring within 7 days |
