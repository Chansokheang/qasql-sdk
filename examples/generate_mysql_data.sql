-- ============================================================
-- QA-SQL MySQL Test Data
-- E-Commerce sample database
--
-- Usage:
--   mysql -u root -p < generate_mysql_data.sql
--   OR paste into MySQL Workbench and run
-- ============================================================

CREATE DATABASE IF NOT EXISTS `qasql_test`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `qasql_test`;

-- ============================================================
-- DROP TABLES (safe re-run)
-- ============================================================

DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `customers`;

-- ============================================================
-- CREATE TABLES
-- ============================================================

CREATE TABLE `customers` (
  `id`            INT AUTO_INCREMENT PRIMARY KEY,
  `name`          VARCHAR(100) NOT NULL,
  `email`         VARCHAR(150) NOT NULL UNIQUE,
  `phone`         VARCHAR(20),
  `city`          VARCHAR(80),
  `country`       VARCHAR(80),
  `registered_at` DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `categories` (
  `id`          INT AUTO_INCREMENT PRIMARY KEY,
  `name`        VARCHAR(80) NOT NULL UNIQUE,
  `description` TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `products` (
  `id`          INT AUTO_INCREMENT PRIMARY KEY,
  `category_id` INT NOT NULL,
  `name`        VARCHAR(150) NOT NULL,
  `description` TEXT,
  `price`       DECIMAL(10,2) NOT NULL,
  `stock_qty`   INT NOT NULL DEFAULT 0,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `orders` (
  `id`           INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id`  INT NOT NULL,
  `status`       ENUM('pending','processing','shipped','delivered','cancelled') NOT NULL,
  `total_amount` DECIMAL(10,2) NOT NULL,
  `ordered_at`   DATETIME NOT NULL,
  `shipped_at`   DATETIME,
  FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `order_items` (
  `id`         INT AUTO_INCREMENT PRIMARY KEY,
  `order_id`   INT NOT NULL,
  `product_id` INT NOT NULL,
  `qty`        INT NOT NULL,
  `unit_price` DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (`order_id`)   REFERENCES `orders`(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- CATEGORIES (7 rows)
-- ============================================================

INSERT INTO `categories` (`name`, `description`) VALUES
  ('Electronics',   'Gadgets, devices, and tech accessories'),
  ('Clothing',      'Apparel for men, women, and children'),
  ('Books',         'Fiction, non-fiction, and educational materials'),
  ('Home & Garden', 'Furniture, decor, and gardening supplies'),
  ('Sports',        'Equipment and gear for sports and outdoor activities'),
  ('Toys',          'Toys and games for all ages'),
  ('Food & Drink',  'Packaged foods, beverages, and snacks');

-- ============================================================
-- PRODUCTS (30 rows)
-- ============================================================

INSERT INTO `products` (`category_id`, `name`, `description`, `price`, `stock_qty`) VALUES
  (1, 'Wireless Bluetooth Headphones', 'High-quality wireless bluetooth headphones available in our store.', 79.99, 120),
  (1, 'Mechanical Keyboard',           'High-quality mechanical keyboard available in our store.',           109.99,  85),
  (1, 'USB-C Hub 7-in-1',              'High-quality usb-c hub 7-in-1 available in our store.',              39.99, 200),
  (1, '27" 4K Monitor',                'High-quality 27" 4k monitor available in our store.',               349.99,  45),
  (1, 'Noise Cancelling Earbuds',      'High-quality noise cancelling earbuds available in our store.',      59.99, 150),
  (1, 'Portable SSD 1TB',              'High-quality portable ssd 1tb available in our store.',              89.99,  70),
  (1, 'Webcam 1080p',                  'High-quality webcam 1080p available in our store.',                  49.99, 110),
  (2, 'Men''s Running Shoes',          'High-quality men''s running shoes available in our store.',          85.00, 300),
  (2, 'Women''s Yoga Pants',           'High-quality women''s yoga pants available in our store.',           45.00, 250),
  (2, 'Unisex Hoodie',                 'High-quality unisex hoodie available in our store.',                 55.00, 180),
  (2, 'Slim Fit Chinos',               'High-quality slim fit chinos available in our store.',               50.00, 160),
  (2, 'Winter Jacket',                 'High-quality winter jacket available in our store.',                129.00,  90),
  (3, 'Python Programming Guide',      'High-quality python programming guide available in our store.',      29.99, 500),
  (3, 'The Art of SQL',                'High-quality the art of sql available in our store.',                34.99, 300),
  (3, 'Clean Code',                    'High-quality clean code available in our store.',                    32.99, 220),
  (3, 'Data Science Handbook',         'High-quality data science handbook available in our store.',         39.99, 180),
  (4, 'Ergonomic Office Chair',        'High-quality ergonomic office chair available in our store.',       299.99,  40),
  (4, 'Standing Desk',                 'High-quality standing desk available in our store.',                399.99,  25),
  (4, 'Indoor Plant Set',              'High-quality indoor plant set available in our store.',              24.99, 200),
  (4, 'Scented Candle Pack',           'High-quality scented candle pack available in our store.',           18.99, 350),
  (5, 'Yoga Mat',                      'High-quality yoga mat available in our store.',                      29.99, 400),
  (5, 'Resistance Bands Set',          'High-quality resistance bands set available in our store.',          19.99, 300),
  (5, 'Adjustable Dumbbells',          'High-quality adjustable dumbbells available in our store.',         149.99,  60),
  (5, 'Running Backpack',              'High-quality running backpack available in our store.',               49.99, 130),
  (6, 'LEGO Classic Bricks Set',       'High-quality lego classic bricks set available in our store.',       49.99, 200),
  (6, 'Board Game: Strategy Quest',    'High-quality board game: strategy quest available in our store.',    39.99, 150),
  (6, 'Remote Control Car',            'High-quality remote control car available in our store.',            34.99, 180),
  (7, 'Premium Coffee Beans 1kg',      'High-quality premium coffee beans 1kg available in our store.',      22.99, 500),
  (7, 'Assorted Herbal Tea Box',       'High-quality assorted herbal tea box available in our store.',       14.99, 400),
  (7, 'Protein Bar Variety Pack',      'High-quality protein bar variety pack available in our store.',      29.99, 350);

-- ============================================================
-- CUSTOMERS (50 rows)
-- ============================================================

INSERT INTO `customers` (`name`, `email`, `phone`, `city`, `country`, `registered_at`) VALUES
  ('Alice Smith',    'alice.smith@example.com',    '+1-212-555-1001', 'New York',     'USA',         '2024-01-15 09:23:00'),
  ('Bob Johnson',    'bob.johnson@example.com',    '+1-310-555-1002', 'Los Angeles',  'USA',         '2024-02-03 14:10:00'),
  ('Charlie Brown',  'charlie.brown@example.com',  '+1-312-555-1003', 'Chicago',      'USA',         '2024-01-28 11:05:00'),
  ('Diana Williams', 'diana.williams@example.com', '+1-713-555-1004', 'Houston',      'USA',         '2023-11-19 08:45:00'),
  ('Eve Garcia',     'eve.garcia@example.com',     '+1-602-555-1005', 'Phoenix',      'USA',         '2024-03-07 16:30:00'),
  ('Frank Miller',   'frank.miller@example.com',   '+44-20-5551006',  'London',       'UK',          '2023-12-01 10:00:00'),
  ('Grace Davis',    'grace.davis@example.com',    '+44-161-5551007', 'Manchester',   'UK',          '2024-02-14 13:20:00'),
  ('Henry Wilson',   'henry.wilson@example.com',   '+1-416-555-1008', 'Toronto',      'Canada',      '2023-10-22 09:15:00'),
  ('Iris Taylor',    'iris.taylor@example.com',    '+1-604-555-1009', 'Vancouver',    'Canada',      '2024-01-05 15:40:00'),
  ('Jack Anderson',  'jack.anderson@example.com',  '+61-2-55551010',  'Sydney',       'Australia',   '2023-09-30 12:00:00'),
  ('Karen Thomas',   'karen.thomas@example.com',   '+61-3-55551011',  'Melbourne',    'Australia',   '2024-03-11 08:30:00'),
  ('Leo Martin',     'leo.martin@example.com',     '+33-1-55551012',  'Paris',        'France',      '2023-11-05 17:00:00'),
  ('Mia Thompson',   'mia.thompson@example.com',   '+49-30-5551013',  'Berlin',       'Germany',     '2024-02-20 11:45:00'),
  ('Nathan Moore',   'nathan.moore@example.com',   '+81-3-55551014',  'Tokyo',        'Japan',       '2023-08-18 09:00:00'),
  ('Olivia Jackson', 'olivia.jackson@example.com', '+82-2-55551015',  'Seoul',        'South Korea', '2024-01-25 14:55:00'),
  ('Paul White',     'paul.white@example.com',     '+66-2-55551016',  'Bangkok',      'Thailand',    '2023-12-15 10:30:00'),
  ('Quinn Harris',   'quinn.harris@example.com',   '+65-6-5551017',   'Singapore',    'Singapore',   '2024-03-01 16:00:00'),
  ('Rachel Lewis',   'rachel.lewis@example.com',   '+971-4-5551018',  'Dubai',        'UAE',         '2023-10-10 13:10:00'),
  ('Sam Clark',      'sam.clark@example.com',      '+1-213-555-1019', 'Los Angeles',  'USA',         '2024-02-08 09:50:00'),
  ('Tina Walker',    'tina.walker@example.com',    '+1-281-555-1020', 'Houston',      'USA',         '2023-11-28 15:25:00'),
  ('Uma Hall',       'uma.hall@example.com',       '+44-20-5551021',  'London',       'UK',          '2024-01-18 11:15:00'),
  ('Victor Allen',   'victor.allen@example.com',   '+1-647-555-1022', 'Toronto',      'Canada',      '2023-09-14 08:00:00'),
  ('Wendy Young',    'wendy.young@example.com',    '+61-8-55551023',  'Sydney',       'Australia',   '2024-03-05 14:40:00'),
  ('Xavier King',    'xavier.king@example.com',    '+33-1-55551024',  'Paris',        'France',      '2023-12-22 10:20:00'),
  ('Yara Scott',     'yara.scott@example.com',     '+49-89-5551025',  'Berlin',       'Germany',     '2024-02-01 16:45:00'),
  ('Zack Green',     'zack.green@example.com',     '+81-6-55551026',  'Tokyo',        'Japan',       '2023-10-05 09:30:00'),
  ('Amy Baker',      'amy.baker@example.com',      '+1-480-555-1027', 'Phoenix',      'USA',         '2024-01-10 13:00:00'),
  ('Brian Adams',    'brian.adams@example.com',    '+1-773-555-1028', 'Chicago',      'USA',         '2023-11-12 15:50:00'),
  ('Clara Nelson',   'clara.nelson@example.com',   '+44-113-5551029', 'Manchester',   'UK',          '2024-02-25 10:05:00'),
  ('David Carter',   'david.carter@example.com',   '+1-778-555-1030', 'Vancouver',    'Canada',      '2023-08-29 08:20:00'),
  ('Emma Mitchell',  'emma.mitchell@example.com',  '+61-7-55551031',  'Melbourne',    'Australia',   '2024-03-15 14:10:00'),
  ('Finn Perez',     'finn.perez@example.com',     '+65-9-5551032',   'Singapore',    'Singapore',   '2023-12-08 11:30:00'),
  ('Gina Roberts',   'gina.roberts@example.com',   '+82-51-5551033',  'Seoul',        'South Korea', '2024-01-30 09:45:00'),
  ('Hugo Turner',    'hugo.turner@example.com',    '+66-53-5551034',  'Bangkok',      'Thailand',    '2023-10-18 16:20:00'),
  ('Isla Phillips',  'isla.phillips@example.com',  '+971-2-5551035',  'Dubai',        'UAE',         '2024-02-12 13:55:00'),
  ('Jake Campbell',  'jake.campbell@example.com',  '+1-214-555-1036', 'Houston',      'USA',         '2023-09-06 10:10:00'),
  ('Kira Parker',    'kira.parker@example.com',    '+1-646-555-1037', 'New York',     'USA',         '2024-03-20 15:00:00'),
  ('Liam Evans',     'liam.evans@example.com',     '+44-20-5551038',  'London',       'UK',          '2023-11-25 09:25:00'),
  ('Maya Edwards',   'maya.edwards@example.com',   '+33-4-55551039',  'Paris',        'France',      '2024-01-22 14:35:00'),
  ('Noah Collins',   'noah.collins@example.com',   '+49-40-5551040',  'Berlin',       'Germany',     '2023-12-30 11:50:00'),
  ('Ora Stewart',    'ora.stewart@example.com',     '+81-3-55551041', 'Tokyo',        'Japan',       '2024-02-18 08:15:00'),
  ('Pete Sanchez',   'pete.sanchez@example.com',   '+1-604-555-1042', 'Vancouver',    'Canada',      '2023-10-01 15:30:00'),
  ('Rosa Morris',    'rosa.morris@example.com',    '+61-2-55551043',  'Sydney',       'Australia',   '2024-03-09 12:40:00'),
  ('Sean Rogers',    'sean.rogers@example.com',    '+65-8-5551044',   'Singapore',    'Singapore',   '2023-11-08 10:55:00'),
  ('Tara Reed',      'tara.reed@example.com',      '+82-2-55551045',  'Seoul',        'South Korea', '2024-01-14 16:05:00'),
  ('Uri Cook',       'uri.cook@example.com',       '+66-2-55551046',  'Bangkok',      'Thailand',    '2023-09-20 13:15:00'),
  ('Vera Morgan',    'vera.morgan@example.com',    '+971-4-5551047',  'Dubai',        'UAE',         '2024-02-05 09:00:00'),
  ('Will Bell',      'will.bell@example.com',      '+1-312-555-1048', 'Chicago',      'USA',         '2023-12-18 14:20:00'),
  ('Xena Murphy',    'xena.murphy@example.com',    '+44-20-5551049',  'London',       'UK',          '2024-03-03 11:10:00'),
  ('Yuki Bailey',    'yuki.bailey@example.com',    '+81-3-55551050',  'Tokyo',        'Japan',       '2023-10-28 15:45:00');

-- ============================================================
-- ORDERS (60 rows)
-- ============================================================

INSERT INTO `orders` (`customer_id`, `status`, `total_amount`, `ordered_at`, `shipped_at`) VALUES
  ( 1, 'delivered',  189.98, '2025-01-05 10:00:00', '2025-01-07 14:00:00'),
  ( 2, 'delivered',   79.99, '2025-01-06 11:30:00', '2025-01-08 09:00:00'),
  ( 3, 'shipped',    164.99, '2025-01-10 09:15:00', '2025-01-12 11:00:00'),
  ( 4, 'delivered',  349.99, '2025-01-12 14:00:00', '2025-01-14 16:00:00'),
  ( 5, 'delivered',   85.00, '2025-01-15 08:30:00', '2025-01-17 10:00:00'),
  ( 6, 'cancelled',   55.00, '2025-01-18 13:00:00', NULL),
  ( 7, 'delivered',  299.99, '2025-01-20 15:45:00', '2025-01-22 12:00:00'),
  ( 8, 'delivered',  109.99, '2025-01-22 10:20:00', '2025-01-24 09:30:00'),
  ( 9, 'shipped',    219.98, '2025-01-25 09:00:00', '2025-01-27 14:00:00'),
  (10, 'delivered',   59.99, '2025-01-28 11:00:00', '2025-01-30 10:00:00'),
  (11, 'delivered',  399.99, '2025-02-01 14:30:00', '2025-02-03 11:00:00'),
  (12, 'processing',  89.99, '2025-02-03 09:45:00', NULL),
  (13, 'delivered',  164.98, '2025-02-05 10:15:00', '2025-02-07 15:00:00'),
  (14, 'delivered',   49.99, '2025-02-07 13:00:00', '2025-02-09 09:00:00'),
  (15, 'shipped',    129.00, '2025-02-10 08:00:00', '2025-02-12 14:30:00'),
  (16, 'delivered',   45.00, '2025-02-12 15:30:00', '2025-02-14 10:00:00'),
  (17, 'delivered',  149.99, '2025-02-14 10:00:00', '2025-02-16 09:00:00'),
  (18, 'cancelled',   79.99, '2025-02-16 14:00:00', NULL),
  (19, 'delivered',  209.98, '2025-02-18 09:30:00', '2025-02-20 11:00:00'),
  (20, 'delivered',   39.99, '2025-02-20 11:00:00', '2025-02-22 14:00:00'),
  (21, 'shipped',    189.98, '2025-02-22 14:15:00', '2025-02-24 10:00:00'),
  (22, 'delivered',  109.99, '2025-02-24 10:30:00', '2025-02-26 09:30:00'),
  (23, 'delivered',   29.99, '2025-02-26 09:00:00', '2025-02-28 11:00:00'),
  (24, 'processing',  59.99, '2025-02-28 13:45:00', NULL),
  (25, 'delivered',  349.99, '2025-03-01 08:15:00', '2025-03-03 14:00:00'),
  (26, 'delivered',   85.00, '2025-03-02 10:00:00', '2025-03-04 09:00:00'),
  (27, 'shipped',     50.00, '2025-03-04 14:30:00', '2025-03-06 11:00:00'),
  (28, 'delivered',  299.99, '2025-03-05 09:15:00', '2025-03-07 15:00:00'),
  (29, 'delivered',   89.99, '2025-03-07 11:00:00', '2025-03-09 10:00:00'),
  (30, 'cancelled',   79.99, '2025-03-08 15:00:00', NULL),
  (31, 'delivered',  164.98, '2025-03-10 08:30:00', '2025-03-12 14:00:00'),
  (32, 'delivered',   49.99, '2025-03-11 13:00:00', '2025-03-13 09:00:00'),
  (33, 'processing',  55.00, '2025-03-12 10:45:00', NULL),
  (34, 'delivered',  129.00, '2025-03-13 09:00:00', '2025-03-15 11:00:00'),
  (35, 'shipped',    399.99, '2025-03-14 14:15:00', '2025-03-16 10:00:00'),
  (36, 'delivered',   45.00, '2025-03-15 10:30:00', '2025-03-17 09:30:00'),
  (37, 'delivered',  209.98, '2025-03-16 09:00:00', '2025-03-18 14:00:00'),
  (38, 'cancelled',   39.99, '2025-03-17 13:45:00', NULL),
  (39, 'delivered',  149.99, '2025-03-18 08:15:00', '2025-03-20 11:00:00'),
  (40, 'delivered',  109.99, '2025-03-19 10:00:00', '2025-03-21 09:00:00'),
  (41, 'shipped',     79.99, '2025-03-20 14:30:00', '2025-03-22 14:00:00'),
  (42, 'delivered',   29.99, '2025-03-01 09:15:00', '2025-03-03 10:00:00'),
  (43, 'delivered',   59.99, '2025-03-02 11:00:00', '2025-03-04 11:00:00'),
  (44, 'processing',  85.00, '2025-03-03 15:00:00', NULL),
  (45, 'delivered',  349.99, '2025-03-04 08:30:00', '2025-03-06 14:00:00'),
  (46, 'delivered',   89.99, '2025-03-05 13:00:00', '2025-03-07 09:00:00'),
  (47, 'shipped',     50.00, '2025-03-06 10:45:00', '2025-03-08 11:00:00'),
  (48, 'delivered',  164.98, '2025-03-07 09:00:00', '2025-03-09 15:00:00'),
  (49, 'delivered',   49.99, '2025-03-08 14:15:00', '2025-03-10 10:00:00'),
  (50, 'cancelled',  299.99, '2025-03-09 10:30:00', NULL),
  ( 1, 'delivered',  109.99, '2025-03-10 09:00:00', '2025-03-12 09:00:00'),
  ( 5, 'delivered',   39.99, '2025-03-11 13:45:00', '2025-03-13 11:00:00'),
  (10, 'shipped',    129.00, '2025-03-12 08:15:00', '2025-03-14 14:00:00'),
  (15, 'delivered',   55.00, '2025-03-13 10:00:00', '2025-03-15 09:00:00'),
  (20, 'processing',  79.99, '2025-03-14 14:30:00', NULL),
  (25, 'delivered',  149.99, '2025-03-15 09:15:00', '2025-03-17 11:00:00'),
  (30, 'delivered',   89.99, '2025-03-16 11:00:00', '2025-03-18 10:00:00'),
  (35, 'pending',     59.99, '2025-03-20 15:00:00', NULL),
  (40, 'pending',    399.99, '2025-03-21 08:30:00', NULL),
  (45, 'pending',     45.00, '2025-03-22 13:00:00', NULL);

-- ============================================================
-- ORDER ITEMS
-- ============================================================

INSERT INTO `order_items` (`order_id`, `product_id`, `qty`, `unit_price`) VALUES
  ( 1,  1, 1,  79.99), ( 1,  5, 1,  59.99), ( 1,  3, 1,  39.99),
  ( 2,  1, 1,  79.99),
  ( 3,  2, 1, 109.99), ( 3,  5, 1,  59.99),
  ( 4,  4, 1, 349.99),
  ( 5,  8, 1,  85.00),
  ( 6, 10, 1,  55.00),
  ( 7, 17, 1, 299.99),
  ( 8,  2, 1, 109.99),
  ( 9,  4, 1, 349.99), ( 9,  3, 1,  39.99),  -- approx
  (10,  5, 1,  59.99),
  (11, 18, 1, 399.99),
  (12,  6, 1,  89.99),
  (13,  2, 1, 109.99), (13,  3, 1,  39.99),
  (14, 14, 1,  49.99),
  (15, 12, 1, 129.00),
  (16,  9, 1,  45.00),
  (17, 23, 1, 149.99),
  (18,  1, 1,  79.99),
  (19,  2, 1, 109.99), (19,  3, 1,  39.99), (19, 21, 1,  29.99),
  (20, 26, 1,  39.99),
  (21,  1, 1,  79.99), (21,  5, 1,  59.99), (21,  3, 1,  39.99),
  (22,  2, 1, 109.99),
  (23, 21, 1,  29.99),
  (24,  5, 1,  59.99),
  (25,  4, 1, 349.99),
  (26,  8, 1,  85.00),
  (27, 11, 1,  50.00),
  (28, 17, 1, 299.99),
  (29,  6, 1,  89.99),
  (30,  1, 1,  79.99),
  (31, 13, 2,  29.99), (31, 15, 1,  32.99), (31, 16, 1,  39.99),
  (32, 14, 1,  49.99),
  (33, 10, 1,  55.00),
  (34, 12, 1, 129.00),
  (35, 18, 1, 399.99),
  (36,  9, 1,  45.00),
  (37,  2, 1, 109.99), (37, 28, 2,  22.99), (37, 29, 2,  14.99),
  (38, 26, 1,  39.99),
  (39, 23, 1, 149.99),
  (40,  2, 1, 109.99),
  (41,  1, 1,  79.99),
  (42, 21, 1,  29.99),
  (43,  5, 1,  59.99),
  (44,  8, 1,  85.00),
  (45,  4, 1, 349.99),
  (46,  6, 1,  89.99),
  (47, 11, 1,  50.00),
  (48, 13, 2,  29.99), (48, 15, 1,  32.99), (48, 16, 1,  39.99),
  (49, 14, 1,  49.99),
  (50, 17, 1, 299.99),
  (51,  2, 1, 109.99),
  (52, 26, 1,  39.99),
  (53, 12, 1, 129.00),
  (54, 10, 1,  55.00),
  (55,  1, 1,  79.99),
  (56, 23, 1, 149.99),
  (57,  6, 1,  89.99),
  (58,  5, 1,  59.99),
  (59,  4, 1, 399.99),
  (60,  9, 1,  45.00);

-- ============================================================
-- VERIFY
-- ============================================================

SELECT 'customers'  AS `table`, COUNT(*) AS `rows` FROM `customers`
UNION ALL
SELECT 'categories',              COUNT(*)          FROM `categories`
UNION ALL
SELECT 'products',                COUNT(*)          FROM `products`
UNION ALL
SELECT 'orders',                  COUNT(*)          FROM `orders`
UNION ALL
SELECT 'order_items',             COUNT(*)          FROM `order_items`;
