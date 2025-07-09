DROP TABLE IF EXISTS stock_transactions;

CREATE TABLE stock_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE,
    from_location_id INTEGER,
    to_location_id INTEGER,
    status TEXT DEFAULT 'Preparing' CHECK(status IN ('Preparing', 'Sent Out', 'Pending', 'Delivered', 'Received')),
    initiated_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO stock_transactions (transaction_id, invoice_number, from_location_id, to_location_id, status, initiated_by, created_at, updated_at) VALUES
(2, 'HQ-C-070725', 1, 3, 'Received', 'HQ', '2025-07-07 10:28:51', '2025-07-07 11:04:05');
