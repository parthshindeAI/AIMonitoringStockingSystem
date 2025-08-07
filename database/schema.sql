CREATE TABLE IF NOT EXISTS Items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS StockLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    current_stock INTEGER NOT NULL,
    usage_today INTEGER NOT NULL,
    damaged_stock INTEGER,
    delivery_quantity INTEGER,
    date TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES Items(id)
);
