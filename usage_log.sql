DROP TABLE IF EXISTS usage_log;

CREATE TABLE usage_log (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    purpose TEXT,
    used_by TEXT,
    location TEXT,
    date_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO usage_log (id, product_id, quantity, purpose, used_by, location, date_used) VALUES
(1, 902, 2, 'Sold to Customer', 'Citibella', 'Citibella', '2025-06-30 16:25:31'),
(2, 926, 1, 'Sold to Customer', 'Citibella', 'Citibella', '2025-06-30 16:25:53'),
(3, 928, 1, 'Sold to Customer', 'Citibella', 'Citibella', '2025-06-30 16:26:05');
