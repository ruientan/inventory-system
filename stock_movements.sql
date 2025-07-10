DROP TABLE IF EXISTS stock_movements;

CREATE TABLE stock_movements (
    movement_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    from_location INTEGER,
    to_location INTEGER,
    quantity INTEGER,
    date_moved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    moved_by TEXT,
    invoice_number TEXT,
    purpose TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (from_location) REFERENCES locations(location_id),
    FOREIGN KEY (to_location) REFERENCES locations(location_id)
);

-- Indexes to speed up filtering/searching
CREATE INDEX idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_from_location ON stock_movements(from_location);
CREATE INDEX idx_stock_movements_to_location ON stock_movements(to_location);


INSERT INTO stock_movements (
    movement_id, product_id, from_location, to_location, quantity,
    date_moved, moved_by, invoice_number, purpose
) VALUES
(7,1012,1,2,2,'2025-06-27 15:02:26','HQ',NULL,NULL),
(8,1010,1,2,1,'2025-06-27 15:02:26','HQ',NULL,NULL),
(9,1011,1,2,1,'2025-06-27 15:02:26','HQ',NULL,NULL),
(10,979,1,3,2,'2025-06-27 17:17:23','HQ',NULL,NULL),
(11,816,1,3,1,'2025-06-27 17:17:23','HQ',NULL,NULL),
(12,839,1,3,2,'2025-06-27 17:37:21','HQ',NULL,NULL),
(13,838,1,3,1,'2025-06-27 17:37:21','HQ',NULL,NULL),
(14,949,1,3,2,'2025-06-30 11:43:23','HQ',NULL,NULL),
(15,944,1,3,2,'2025-06-30 11:43:23','HQ',NULL,NULL),
(16,887,1,3,1,'2025-06-30 11:43:23','HQ',NULL,NULL),
(17,973,1,3,1,'2025-06-30 11:43:23','HQ',NULL,NULL),
(18,801,1,3,2,'2025-06-30 11:43:23','HQ',NULL,NULL),
(19,863,NULL,1,6,'2025-06-30 14:57:54','Raine',NULL,'Restock'),
(20,1018,NULL,1,0,'2025-06-30 15:07:13','Raine',NULL,'New Product'),
(21,1019,NULL,1,8,'2025-06-30 16:19:55','Raine',NULL,'New Product'),
(22,902,2,NULL,2,'2025-06-30 16:25:31','Mbella',NULL,'Sold to Customer'),
(23,926,2,NULL,1,'2025-06-30 16:25:53','Mbella',NULL,'Sold to Customer'),
(24,928,2,NULL,1,'2025-06-30 16:26:05','Mbella',NULL,'Sold to Customer'),
(27,896,1,3,2,'2025-07-01 22:19:18','HQ','HQ-C-010725','Transfer'),
(28,898,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(29,902,1,3,2,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(30,926,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(31,928,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(32,895,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(33,899,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(34,1019,1,3,2,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(35,792,1,3,1,'2025-07-01 22:19:19','HQ','HQ-C-010725','Transfer'),
(36,1014,1,3,2,'2025-07-02 09:44:53','HQ','HQ-C-020725','Transfer'),
(37,903,1,3,2,'2025-07-02 09:44:53','HQ','HQ-C-020725','Transfer'),
(38,1020,NULL,1,50,'2025-07-02 15:20:51','Raine',NULL,'New Product'),
(39,1021,NULL,1,88,'2025-07-02 15:21:15','Raine',NULL,'New Product'),
(40,1022,NULL,1,4,'2025-07-02 15:21:37','Raine',NULL,'New Product'),
(41,1023,NULL,1,1,'2025-07-02 15:22:33','Raine',NULL,'New Product'),
(42,1024,NULL,1,5,'2025-07-02 15:23:06','Raine',NULL,'New Product'),
(43,1025,NULL,1,34,'2025-07-02 15:23:37','Raine',NULL,'New Product'),
(44,1026,NULL,1,12,'2025-07-02 15:24:04','Raine',NULL,'New Product'),
(45,1027,NULL,1,1,'2025-07-02 15:24:23','Raine',NULL,'New Product'),
(46,1028,NULL,1,4,'2025-07-02 15:26:40','Raine',NULL,'New Product'),
(47,801,1,3,6,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),
(48,802,1,3,3,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),
(49,1028,1,3,3,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),
(50,852,1,3,4,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),
(51,863,1,3,4,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(52,851,1,3,4,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(53,763,1,3,11,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(54,765,1,3,12,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(55,767,1,3,3,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(56,764,1,3,10,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(57,777,1,3,6,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(58,778,1,3,5,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(59,781,1,3,5,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(60,817,1,3,3,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(61,807,1,3,2,'2025-07-02 15:36:08','HQ','HQ-C-020725','Transfer'),(62,1029,NULL,1,2,'2025-07-02 15:38:45','Raine',NULL,'New Product'),(63,1030,NULL,1,0,'2025-07-02 15:52:28','Raine',NULL,'New Product'),(64,1031,NULL,1,1,'2025-07-02 15:53:00','Raine',NULL,'New Product'),(65,1032,NULL,1,2,'2025-07-02 15:53:22','Raine',NULL,'New Product'),(66,1033,NULL,1,0,'2025-07-02 15:53:52','Raine',NULL,'New Product'),(67,836,1,3,1,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(68,858,1,3,4,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(69,1029,1,3,2,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(70,816,1,3,1,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(71,890,1,3,2,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(72,891,1,3,3,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(73,842,1,3,2,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(74,1031,1,3,1,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(75,1032,1,3,1,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(76,984,1,3,1,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(77,1022,1,3,6,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(78,1005,1,3,6,'2025-07-02 16:00:48','HQ','HQ-C-020725','Transfer'),(79,888,NULL,1,6,'2025-07-02 16:46:56','Raine',NULL,'Restock'),(80,887,NULL,1,2,'2025-07-02 16:47:37','Raine',NULL,'Restock'),(81,1034,NULL,1,2,'2025-07-02 16:49:32','Raine',NULL,'New Product'),(82,973,NULL,1,2,'2025-07-02 16:50:24','Raine',NULL,'Restock'),(83,1035,NULL,1,6,'2025-07-02 16:52:47','Raine',NULL,'New Product'),(84,947,NULL,1,6,'2025-07-02 16:53:27','Raine',NULL,'Restock'),(85,946,NULL,1,6,'2025-07-02 16:53:42','Raine',NULL,'Restock'),(86,949,NULL,1,6,'2025-07-02 16:54:02','Raine',NULL,'Restock'),(87,944,NULL,1,6,'2025-07-02 16:55:33','Raine',NULL,'Restock'),(88,928,NULL,1,3,'2025-07-02 16:55:44','Raine',NULL,'Restock'),(89,932,NULL,1,3,'2025-07-02 16:56:05','Raine',NULL,'Restock'),(90,933,NULL,1,3,'2025-07-02 16:56:21','Raine',NULL,'Restock'),(91,903,NULL,1,3,'2025-07-02 16:56:39','Raine',NULL,'Restock'),(92,902,NULL,1,3,'2025-07-02 16:56:51','Raine',NULL,'Restock'),(93,1018,NULL,1,3,'2025-07-02 16:57:04','Raine',NULL,'Restock'),(94,901,NULL,1,3,'2025-07-02 16:57:25','Raine',NULL,'Restock'),(95,955,NULL,1,3,'2025-07-02 16:57:39','Raine',NULL,'Restock'),(96,1036,NULL,1,3,'2025-07-02 16:59:11','Raine',NULL,'New Product'),(97,1037,NULL,1,3,'2025-07-02 17:00:03','Raine',NULL,'New Product'),(98,926,NULL,1,3,'2025-07-02 17:00:17','Raine',NULL,'Restock'),(99,939,NULL,1,2,'2025-07-02 17:00:34','Raine',NULL,'Restock'),(100,938,NULL,1,2,'2025-07-02 17:00:44','Raine',NULL,'Restock'),(101,965,1,3,1,'2025-07-02 18:15:17','HQ','HQ-C-020725','Transfer'),(102,966,1,3,1,'2025-07-02 18:15:17','HQ','HQ-C-020725','Transfer'),(103,790,1,3,2,'2025-07-02 18:15:17','HQ','HQ-C-020725','Transfer'),(104,957,1,3,1,'2025-07-02 18:15:17','HQ','HQ-C-020725','Transfer'),(105,968,1,3,15,'2025-07-02 18:15:17','HQ','HQ-C-020725','Transfer'),(106,896,1,3,2,'2025-07-04 12:22:51','HQ_Staff',NULL,'Manual Fix'),(107,926,1,3,1,'2025-07-04 12:26:13','HQ_Staff',NULL,'Manual Fix'),(108,928,1,3,1,'2025-07-04 12:29:51','HQ_Staff',NULL,'Manual Fix'),(109,895,1,3,1,'2025-07-04 12:33:23','HQ_Staff',NULL,'Manual Fix'),(110,899,1,3,1,'2025-07-04 12:36:35','HQ_Staff',NULL,'Manual Fix'),(111,1019,1,3,2,'2025-07-04 12:38:57','HQ_Staff',NULL,'Manual Fix'),(112,792,1,3,1,'2025-07-04 12:41:32','HQ_Staff',NULL,'Manual Fix'),(113,792,NULL,1,12,'2025-07-04 13:31:57','Raine',NULL,'Restock'),(114,1038,NULL,1,3,'2025-07-04 13:33:28','Raine',NULL,'New Product'),(115,1039,NULL,1,6,'2025-07-04 13:34:00','Raine',NULL,'New Product'),(116,1040,NULL,1,2,'2025-07-04 13:34:45','Raine',NULL,'New Product'),(117,1041,NULL,1,2,'2025-07-04 13:37:39','Raine',NULL,'New Product'),(118,1042,NULL,1,2,'2025-07-04 13:38:01','Raine',NULL,'New Product'),(119,1043,NULL,1,1,'2025-07-04 13:38:26','Raine',NULL,'New Product'),(120,1044,NULL,1,2,'2025-07-04 13:38:50','Raine',NULL,'New Product'),(121,1045,NULL,1,1,'2025-07-04 13:39:09','Raine',NULL,'New Product'),(122,1046,NULL,1,2,'2025-07-04 13:39:31','Raine',NULL,'New Product'),(123,1047,NULL,1,1,'2025-07-04 13:39:50','Raine',NULL,'New Product'),(124,1048,NULL,1,2,'2025-07-04 13:40:05','Raine',NULL,'New Product'),(125,1049,NULL,1,1,'2025-07-04 13:40:22','Raine',NULL,'New Product'),(126,1050,NULL,1,4,'2025-07-04 15:15:09','Raine',NULL,'New Product'),(127,1051,NULL,1,1,'2025-07-04 15:15:34','Raine',NULL,'New Product'),(128,1052,NULL,1,7,'2025-07-04 15:16:07','Raine',NULL,'New Product'),(129,1051,1,3,1,'2025-07-04 15:17:47','HQ','HQ-C-040725','Transfer'),(130,1052,1,3,2,'2025-07-04 15:17:47','HQ','HQ-C-040725','Transfer'),(131,883,1,3,2,'2025-07-04 17:31:24','HQ','HQ-C-040725','Transfer'),(132,880,1,3,2,'2025-07-04 17:31:24','HQ','HQ-C-040725','Transfer'),(133,1018,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(134,902,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(135,933,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(136,901,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(137,932,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(138,926,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(139,949,1,3,3,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(140,944,1,3,4,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(141,1041,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(142,1040,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt'),(143,946,1,3,1,'2025-07-07 11:24:04','HQ',NULL,'Auto Deduct HQ on Receipt');

