DROP TABLE IF EXISTS transaction_items;

CREATE TABLE transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (transaction_id) REFERENCES stock_transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);


INSERT INTO transaction_items (id, transaction_id, product_id, quantity) VALUES
(2, 2, 1018, 1),
(3, 2, 902, 1),
(4, 2, 933, 1),
(5, 2, 901, 1),
(6, 2, 932, 1),
(7, 2, 926, 1),
(8, 2, 949, 3),
(9, 2, 944, 4),
(10, 2, 1041, 1),
(11, 2, 1040, 1),
(12, 2, 946, 1);