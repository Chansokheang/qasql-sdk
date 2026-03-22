"""
MySQL Test Data Generator for QA-SQL

Creates a sample e-commerce database in MySQL with realistic data
to test the QA-SQL MySQL connector and text-to-SQL queries.

Schema:
  - customers     (id, name, email, phone, city, country, registered_at)
  - categories    (id, name, description)
  - products      (id, category_id, name, description, price, stock_qty)
  - orders        (id, customer_id, status, total_amount, ordered_at, shipped_at)
  - order_items   (id, order_id, product_id, qty, unit_price)

Prerequisites:
    pip install mysql-connector-python
    OR
    pip install pymysql

    MySQL server must be running and accessible.

Configuration (env vars or edit defaults below):
    export MYSQL_HOST='localhost'
    export MYSQL_PORT='3306'
    export MYSQL_USER='root'
    export MYSQL_PASSWORD='password'
    export MYSQL_DATABASE='qasql_test'   # will be created if missing

Usage:
    python generate_mysql_data.py
    python generate_mysql_data.py --reset   # drop & recreate tables
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta

# ============================================================
# Configuration
# ============================================================

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "qasql_test")


# ============================================================
# Sample Data
# ============================================================

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Iris", "Jack", "Karen", "Leo", "Mia", "Nathan", "Olivia", "Paul",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
    "Yara", "Zack", "Amy", "Brian", "Clara", "David",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White",
    "Harris", "Martin", "Thompson", "Moore", "Young", "Lee",
]

CITIES = [
    ("New York", "USA"), ("Los Angeles", "USA"), ("Chicago", "USA"),
    ("Houston", "USA"), ("Phoenix", "USA"), ("London", "UK"),
    ("Manchester", "UK"), ("Toronto", "Canada"), ("Vancouver", "Canada"),
    ("Sydney", "Australia"), ("Melbourne", "Australia"), ("Paris", "France"),
    ("Berlin", "Germany"), ("Tokyo", "Japan"), ("Seoul", "South Korea"),
    ("Bangkok", "Thailand"), ("Singapore", "Singapore"), ("Dubai", "UAE"),
]

CATEGORIES = [
    ("Electronics",   "Gadgets, devices, and tech accessories"),
    ("Clothing",      "Apparel for men, women, and children"),
    ("Books",         "Fiction, non-fiction, and educational materials"),
    ("Home & Garden", "Furniture, decor, and gardening supplies"),
    ("Sports",        "Equipment and gear for sports and outdoor activities"),
    ("Toys",          "Toys and games for all ages"),
    ("Food & Drink",  "Packaged foods, beverages, and snacks"),
]

PRODUCTS = [
    # (category_idx 1-based, name, price, stock)
    (1, "Wireless Bluetooth Headphones",   79.99,  120),
    (1, "Mechanical Keyboard",            109.99,   85),
    (1, "USB-C Hub 7-in-1",               39.99,  200),
    (1, "27\" 4K Monitor",               349.99,   45),
    (1, "Noise Cancelling Earbuds",        59.99,  150),
    (1, "Portable SSD 1TB",               89.99,   70),
    (1, "Webcam 1080p",                   49.99,  110),
    (2, "Men's Running Shoes",             85.00,  300),
    (2, "Women's Yoga Pants",              45.00,  250),
    (2, "Unisex Hoodie",                   55.00,  180),
    (2, "Slim Fit Chinos",                 50.00,  160),
    (2, "Winter Jacket",                  129.00,   90),
    (3, "Python Programming Guide",        29.99,  500),
    (3, "The Art of SQL",                  34.99,  300),
    (3, "Clean Code",                      32.99,  220),
    (3, "Data Science Handbook",           39.99,  180),
    (4, "Ergonomic Office Chair",         299.99,   40),
    (4, "Standing Desk",                  399.99,   25),
    (4, "Indoor Plant Set",                24.99,  200),
    (4, "Scented Candle Pack",             18.99,  350),
    (5, "Yoga Mat",                        29.99,  400),
    (5, "Resistance Bands Set",            19.99,  300),
    (5, "Adjustable Dumbbells",           149.99,   60),
    (5, "Running Backpack",                49.99,  130),
    (6, "LEGO Classic Bricks Set",         49.99,  200),
    (6, "Board Game: Strategy Quest",      39.99,  150),
    (6, "Remote Control Car",              34.99,  180),
    (7, "Premium Coffee Beans 1kg",        22.99,  500),
    (7, "Assorted Herbal Tea Box",         14.99,  400),
    (7, "Protein Bar Variety Pack",        29.99,  350),
]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
STATUS_WEIGHTS = [0.05, 0.10, 0.20, 0.60, 0.05]


# ============================================================
# Helpers
# ============================================================

def get_connection(database=None):
    """Create a MySQL connection, trying mysql.connector then pymysql."""
    db = database or MYSQL_DATABASE
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=db if db else None,
            use_pure=True,
            autocommit=False,
        )
        return conn, "mysql.connector"
    except ImportError:
        pass

    try:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=db if db else None,
            autocommit=False,
            cursorclass=pymysql.cursors.Cursor,
        )
        return conn, "pymysql"
    except ImportError:
        pass

    print("ERROR: No MySQL driver found.")
    print("  Install with: pip install mysql-connector-python")
    print("       or:      pip install pymysql")
    sys.exit(1)


def random_date(start_days_ago: int, end_days_ago: int = 0) -> datetime:
    delta = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=delta, hours=random.randint(0, 23), minutes=random.randint(0, 59))


# ============================================================
# Setup
# ============================================================

def create_database(reset: bool):
    """Create the database if it doesn't exist."""
    conn, driver = get_connection(database=None)
    cursor = conn.cursor()

    if reset:
        cursor.execute(f"DROP DATABASE IF EXISTS `{MYSQL_DATABASE}`")
        print(f"  Dropped database '{MYSQL_DATABASE}'")

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    print(f"  Database '{MYSQL_DATABASE}' ready  (driver: {driver})")
    conn.commit()
    cursor.close()
    conn.close()


def create_tables(reset: bool):
    """Create all tables."""
    conn, _ = get_connection()
    cursor = conn.cursor()

    if reset:
        for tbl in ["order_items", "orders", "products", "categories", "customers"]:
            cursor.execute(f"DROP TABLE IF EXISTS `{tbl}`")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `customers` (
            `id`            INT AUTO_INCREMENT PRIMARY KEY,
            `name`          VARCHAR(100) NOT NULL,
            `email`         VARCHAR(150) NOT NULL UNIQUE,
            `phone`         VARCHAR(20),
            `city`          VARCHAR(80),
            `country`       VARCHAR(80),
            `registered_at` DATETIME NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `categories` (
            `id`          INT AUTO_INCREMENT PRIMARY KEY,
            `name`        VARCHAR(80) NOT NULL UNIQUE,
            `description` TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `products` (
            `id`          INT AUTO_INCREMENT PRIMARY KEY,
            `category_id` INT NOT NULL,
            `name`        VARCHAR(150) NOT NULL,
            `description` TEXT,
            `price`       DECIMAL(10,2) NOT NULL,
            `stock_qty`   INT NOT NULL DEFAULT 0,
            FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `orders` (
            `id`           INT AUTO_INCREMENT PRIMARY KEY,
            `customer_id`  INT NOT NULL,
            `status`       ENUM('pending','processing','shipped','delivered','cancelled') NOT NULL,
            `total_amount` DECIMAL(10,2) NOT NULL,
            `ordered_at`   DATETIME NOT NULL,
            `shipped_at`   DATETIME,
            FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `order_items` (
            `id`         INT AUTO_INCREMENT PRIMARY KEY,
            `order_id`   INT NOT NULL,
            `product_id` INT NOT NULL,
            `qty`        INT NOT NULL,
            `unit_price` DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (`order_id`)   REFERENCES `orders`(`id`),
            FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("  Tables created.")


# ============================================================
# Data insertion
# ============================================================

def insert_customers(cursor, n: int = 60) -> list[int]:
    """Insert n customers, return list of inserted IDs."""
    print(f"  Inserting {n} customers...")
    ids = []
    used_emails = set()
    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"
        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@example.com"
        # ensure unique emails
        suffix = 1
        while email in used_emails:
            email = f"{base_email}{suffix}@example.com"
            suffix += 1
        used_emails.add(email)
        phone   = f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        city, country = random.choice(CITIES)
        reg_at  = random_date(730, 30)  # registered 1 month – 2 years ago

        cursor.execute("""
            INSERT IGNORE INTO `customers` (`name`, `email`, `phone`, `city`, `country`, `registered_at`)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, phone, city, country, reg_at))
        ids.append(cursor.lastrowid if cursor.lastrowid else None)

    # fetch real IDs in case of IGNORE skips
    cursor.execute("SELECT `id` FROM `customers`")
    return [row[0] for row in cursor.fetchall()]


def insert_categories(cursor) -> list[int]:
    """Insert categories, return IDs."""
    print(f"  Inserting {len(CATEGORIES)} categories...")
    ids = []
    for name, desc in CATEGORIES:
        cursor.execute("""
            INSERT IGNORE INTO `categories` (`name`, `description`) VALUES (%s, %s)
        """, (name, desc))
    cursor.execute("SELECT `id` FROM `categories` ORDER BY `id`")
    return [row[0] for row in cursor.fetchall()]


def insert_products(cursor, category_ids: list[int]) -> list[int]:
    """Insert products, return IDs."""
    print(f"  Inserting {len(PRODUCTS)} products...")
    for cat_idx, name, price, stock in PRODUCTS:
        real_cat_id = category_ids[cat_idx - 1]
        desc = f"High-quality {name.lower()} available in our store."
        cursor.execute("""
            INSERT IGNORE INTO `products` (`category_id`, `name`, `description`, `price`, `stock_qty`)
            VALUES (%s, %s, %s, %s, %s)
        """, (real_cat_id, name, desc, price, stock))
    cursor.execute("SELECT `id` FROM `products` ORDER BY `id`")
    return [row[0] for row in cursor.fetchall()]


def insert_orders(cursor, customer_ids: list[int], product_ids: list[int], n: int = 200):
    """Insert n orders with 1-4 items each."""
    print(f"  Inserting {n} orders with items...")

    # Fetch product prices
    cursor.execute("SELECT `id`, `price` FROM `products`")
    price_map = {row[0]: float(row[1]) for row in cursor.fetchall()}

    for _ in range(n):
        cust_id   = random.choice(customer_ids)
        status    = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS)[0]
        ordered_at = random_date(365, 1)

        shipped_at = None
        if status in ("shipped", "delivered"):
            shipped_at = ordered_at + timedelta(days=random.randint(1, 5))

        # Pick 1-4 distinct products
        num_items = random.randint(1, 4)
        chosen_products = random.sample(product_ids, k=min(num_items, len(product_ids)))

        # Compute total
        total = sum(price_map[pid] * random.randint(1, 3) for pid in chosen_products)

        cursor.execute("""
            INSERT INTO `orders` (`customer_id`, `status`, `total_amount`, `ordered_at`, `shipped_at`)
            VALUES (%s, %s, %s, %s, %s)
        """, (cust_id, status, round(total, 2), ordered_at, shipped_at))

        order_id = cursor.lastrowid

        for pid in chosen_products:
            qty        = random.randint(1, 3)
            unit_price = price_map[pid]
            cursor.execute("""
                INSERT INTO `order_items` (`order_id`, `product_id`, `qty`, `unit_price`)
                VALUES (%s, %s, %s, %s)
            """, (order_id, pid, qty, unit_price))


# ============================================================
# Verification
# ============================================================

def verify(cursor):
    """Print row counts and a few sample queries."""
    tables = ["customers", "categories", "products", "orders", "order_items"]
    print("\n  Row counts:")
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`")
        count = cursor.fetchone()[0]
        print(f"    {tbl:<15} {count:>6} rows")

    print("\n  Top 5 customers by order count:")
    cursor.execute("""
        SELECT c.name, COUNT(o.id) AS order_count, SUM(o.total_amount) AS total_spent
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, c.name
        ORDER BY order_count DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"    {row[0]:<25}  orders: {row[1]}  spent: ${row[2]:.2f}")

    print("\n  Revenue by category:")
    cursor.execute("""
        SELECT cat.name, SUM(oi.qty * oi.unit_price) AS revenue
        FROM order_items oi
        JOIN products p  ON p.id = oi.product_id
        JOIN categories cat ON cat.id = p.category_id
        GROUP BY cat.id, cat.name
        ORDER BY revenue DESC
    """)
    for row in cursor.fetchall():
        print(f"    {row[0]:<20}  ${row[1]:.2f}")

    print("\n  Orders by status:")
    cursor.execute("""
        SELECT status, COUNT(*) AS cnt, SUM(total_amount) AS total
        FROM orders GROUP BY status ORDER BY cnt DESC
    """)
    for row in cursor.fetchall():
        print(f"    {row[0]:<12}  count: {row[1]}  total: ${row[2]:.2f}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate MySQL test data for QA-SQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
After running this script, test with QA-SQL:

  # Terminal UI
  python -m qasql.tui --db mysql://%(user)s:%(password)s@%(host)s:%(port)s/%(db)s

  # Inside the TUI
  /mysql %(host)s %(db)s %(user)s <your_password>

  # Example natural language questions to try:
  How many customers are there?
  What is the total revenue by category?
  Show me the top 5 best-selling products.
  How many orders were delivered last month?
  Which customers spent the most money?
  What is the average order value?
  Show me all pending orders.
  How many orders does each customer have?
""" % {
            "user": MYSQL_USER,
            "password": "****",
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "db": MYSQL_DATABASE,
        }
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Drop and recreate all tables before inserting data"
    )
    parser.add_argument(
        "--customers", type=int, default=60,
        help="Number of customers to generate (default: 60)"
    )
    parser.add_argument(
        "--orders", type=int, default=200,
        help="Number of orders to generate (default: 200)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("QA-SQL - MySQL Test Data Generator")
    print("=" * 60)
    print(f"""
  Host:     {MYSQL_HOST}:{MYSQL_PORT}
  User:     {MYSQL_USER}
  Database: {MYSQL_DATABASE}
  Reset:    {args.reset}
  Customers to insert: {args.customers}
  Orders to insert:    {args.orders}
""")

    # Step 1: Create database
    print("[1/4] Setting up database...")
    create_database(reset=args.reset)

    # Step 2: Create tables
    print("[2/4] Creating tables...")
    create_tables(reset=args.reset)

    # Step 3: Insert data
    print("[3/4] Inserting data...")
    conn, _ = get_connection()
    cursor = conn.cursor()

    try:
        category_ids = insert_categories(cursor)
        product_ids  = insert_products(cursor, category_ids)
        customer_ids = insert_customers(cursor, n=args.customers)
        insert_orders(cursor, customer_ids, product_ids, n=args.orders)
        conn.commit()
        print("  Data committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\nERROR during data insertion: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        conn.close()
        sys.exit(1)

    # Step 4: Verify
    print("[4/4] Verifying data...")
    verify(cursor)

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Done! Database ready for QA-SQL testing.")
    print("=" * 60)
    print(f"""
Connect with QA-SQL Terminal UI:
  python -m qasql.tui --db mysql://{MYSQL_USER}:****@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}

Or set env vars and use --mysql flag:
  export MYSQL_HOST='{MYSQL_HOST}'
  export MYSQL_PORT='{MYSQL_PORT}'
  export MYSQL_DATABASE='{MYSQL_DATABASE}'
  export MYSQL_USER='{MYSQL_USER}'
  export MYSQL_PASSWORD='<your_password>'
  python -m qasql.tui --mysql

Sample questions to try:
  - How many customers are there?
  - What is the total revenue by category?
  - Show me the top 5 best-selling products by quantity sold.
  - How many orders were delivered?
  - Which customers have spent the most?
  - What is the average order value per status?
  - List all products with low stock (less than 50 units).
  - How many orders were placed each month?
""")


if __name__ == "__main__":
    main()
