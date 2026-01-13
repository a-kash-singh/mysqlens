#!/usr/bin/env python3
"""
MySQLens Complex Demo Data Seeder
Creates a high-volume MySQL database with sophisticated performance bottlenecks,
bloat scenarios, and complex schema relationships for testing database optimization.
"""

import asyncio
import aiomysql
import os
import sys
from datetime import datetime, timedelta
import random
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


def get_database_config():
    """Get database configuration from environment."""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'autocommit': True,
        'charset': 'utf8mb4'
    }


async def setup_schema(conn):
    """Create complex schema with multiple tables and relationships."""
    logger.info("Setting up enhanced schema...")
    cursor = await conn.cursor()
    
    try:
        # Create database
        await cursor.execute("CREATE DATABASE IF NOT EXISTS mysqlens_complex")
        await cursor.execute("USE mysqlens_complex")
        
        # Drop existing tables
        await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        tables = [
            'demo_metadata', 'demo_user_activity', 'demo_reviews', 
            'demo_inventory', 'demo_coupons', 'demo_order_items',
            'demo_orders', 'demo_products', 'demo_users'
        ]
        for table in tables:
            await cursor.execute(f"DROP TABLE IF EXISTS {table}")
        await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 1. Users table (with various types for indexing tests)
        await cursor.execute("""
            CREATE TABLE demo_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uuid CHAR(36) DEFAULT (UUID()),
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                is_staff BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile_data JSON
            ) ENGINE=InnoDB
        """)

        # 2. Products table
        await cursor.execute("""
            CREATE TABLE demo_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(100),
                tags JSON,
                attributes JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 3. Inventory table (Heavy write)
        await cursor.execute("""
            CREATE TABLE demo_inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                warehouse_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 0,
                reserved_quantity INT NOT NULL DEFAULT 0,
                last_restock TIMESTAMP NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES demo_products(id)
            ) ENGINE=InnoDB
        """)

        # 4. Coupons table
        await cursor.execute("""
            CREATE TABLE demo_coupons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                discount_percent INT CHECK (discount_percent > 0 AND discount_percent <= 100),
                valid_from TIMESTAMP NOT NULL,
                valid_to TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            ) ENGINE=InnoDB
        """)

        # 5. Orders table (intentionally missing index on user_id)
        await cursor.execute("""
            CREATE TABLE demo_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                coupon_id INT NULL,
                order_status VARCHAR(20) DEFAULT 'pending',
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_address TEXT,
                tracking_number VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES demo_users(id),
                FOREIGN KEY (coupon_id) REFERENCES demo_coupons(id)
            ) ENGINE=InnoDB
        """)

        # 6. Order Items table
        await cursor.execute("""
            CREATE TABLE demo_order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES demo_orders(id),
                FOREIGN KEY (product_id) REFERENCES demo_products(id)
            ) ENGINE=InnoDB
        """)

        # 7. Reviews table (Text heavy, missing index on product_id)
        await cursor.execute("""
            CREATE TABLE demo_reviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                user_id INT NOT NULL,
                rating INT CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                helpful_votes INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES demo_products(id),
                FOREIGN KEY (user_id) REFERENCES demo_users(id)
            ) ENGINE=InnoDB
        """)

        # 8. User Activity (Extremely high volume, intentionally un-indexed)
        await cursor.execute("""
            CREATE TABLE demo_user_activity (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                session_id VARCHAR(100),
                activity_type VARCHAR(50) NOT NULL,
                path TEXT,
                metadata JSON,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES demo_users(id)
            ) ENGINE=InnoDB
        """)

        # 9. Metadata / System Config (Large JSON objects)
        await cursor.execute("""
            CREATE TABLE demo_metadata (
                id INT AUTO_INCREMENT PRIMARY KEY,
                `key` VARCHAR(100) UNIQUE NOT NULL,
                value JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        logger.info("Schema created successfully")

    finally:
        await cursor.close()


async def seed_users(conn, count=2000):
    logger.info(f"Seeding {count} users...")
    cursor = await conn.cursor()
    
    try:
        users = []
        cities = ["New York", "London", "Paris", "Berlin", "Tokyo", "Sydney", "Toronto", "Singapore"]
        
        for i in range(count):
            username = f"user_{i}_{random.randint(1000, 9999)}"
            email = f"{username}@example.com"
            profile = json.dumps({
                "age": random.randint(18, 70),
                "city": random.choice(cities),
                "last_search": "SQL Optimization",
                "preferences": {"theme": "dark", "notifications": True}
            })
            users.append((
                username, email, "pbkdf2:sha256:260000$hashedpassword",
                f"First{i}", f"Last{i}", profile
            ))
        
        await cursor.executemany("""
            INSERT INTO demo_users (username, email, password_hash, first_name, last_name, profile_data)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, users)
        
        logger.info(f"Seeded {count} users")
    finally:
        await cursor.close()


async def seed_products(conn, count=1000):
    logger.info(f"Seeding {count} products...")
    cursor = await conn.cursor()
    
    try:
        categories = ["Electronics", "Home & Garden", "Books", "Clothing", "Toys", "Health"]
        tags_pool = ["premium", "bestseller", "new", "sale", "eco-friendly", "refurbished"]
        colors = ["black", "white", "silver", "red", "blue"]
        
        products = []
        for i in range(count):
            sku = f"SKU-{i:06d}-{random.randint(10, 99)}"
            tags = json.dumps(random.sample(tags_pool, random.randint(1, 3)))
            attrs = json.dumps({
                "weight": f"{random.uniform(0.1, 10.0):.2f}kg",
                "color": random.choice(colors),
                "warranty": random.choice(["1 year", "2 years", "None"])
            })
            products.append((
                sku, f"Product {i}",
                f"High quality {random.choice(categories)} product featuring advanced technology.",
                round(random.uniform(5.0, 2000.0), 2),
                random.choice(categories), tags, attrs
            ))
        
        await cursor.executemany("""
            INSERT INTO demo_products (sku, name, description, price, category, tags, attributes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, products)
        
        logger.info(f"Seeded {count} products")
    finally:
        await cursor.close()


async def seed_inventory(conn):
    logger.info("Seeding inventory...")
    cursor = await conn.cursor()
    
    try:
        await cursor.execute("SELECT id FROM demo_products")
        product_ids = [r[0] for r in await cursor.fetchall()]
        
        inventory = []
        for pid in product_ids:
            for wid in range(1, 3):
                inventory.append((
                    pid, wid, random.randint(0, 1000), random.randint(0, 50)
                ))
        
        await cursor.executemany("""
            INSERT INTO demo_inventory (product_id, warehouse_id, quantity, reserved_quantity)
            VALUES (%s, %s, %s, %s)
        """, inventory)
        
        logger.info(f"Seeded {len(inventory)} inventory records")
    finally:
        await cursor.close()


async def seed_coupons(conn):
    logger.info("Seeding coupons...")
    cursor = await conn.cursor()
    
    try:
        now = datetime.now()
        coupons = [
            ('SAVE10', 10, now - timedelta(days=365), now + timedelta(days=365)),
            ('WELCOME20', 20, now - timedelta(days=30), now + timedelta(days=335)),
            ('EXPIRED', 50, now - timedelta(days=730), now - timedelta(days=365)),
            ('SUMMER25', 25, now - timedelta(days=60), now + timedelta(days=30)),
            ('VIP30', 30, now - timedelta(days=10), now + timedelta(days=355)),
        ]
        
        await cursor.executemany("""
            INSERT INTO demo_coupons (code, discount_percent, valid_from, valid_to)
            VALUES (%s, %s, %s, %s)
        """, coupons)
        
        logger.info(f"Seeded {len(coupons)} coupons")
    finally:
        await cursor.close()


async def seed_orders(conn, count=10000):
    logger.info(f"Seeding {count} orders...")
    cursor = await conn.cursor()
    
    try:
        await cursor.execute("SELECT id FROM demo_users")
        user_ids = [r[0] for r in await cursor.fetchall()]
        
        await cursor.execute("SELECT id, price FROM demo_products")
        products = {r[0]: float(r[1]) for r in await cursor.fetchall()}
        product_ids = list(products.keys())
        
        await cursor.execute("SELECT id FROM demo_coupons")
        coupon_ids = [r[0] for r in await cursor.fetchall()] + [None] * 5
        
        statuses = ['pending', 'shipped', 'delivered', 'cancelled', 'refunded']
        
        for i in range(count):
            user_id = random.choice(user_ids)
            coupon_id = random.choice(coupon_ids)
            status = random.choice(statuses)
            
            await cursor.execute("""
                INSERT INTO demo_orders (user_id, coupon_id, order_status, total_amount, shipping_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, coupon_id, status, 0, "123 Test St, Sandbox City"))
            
            order_id = cursor.lastrowid
            
            num_items = random.randint(1, 5)
            total = 0
            items = []
            
            for _ in range(num_items):
                pid = random.choice(product_ids)
                qty = random.randint(1, 3)
                price = products[pid]
                total += qty * price
                items.append((order_id, pid, qty, price))
            
            await cursor.executemany("""
                INSERT INTO demo_order_items (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, items)
            
            await cursor.execute("UPDATE demo_orders SET total_amount = %s WHERE id = %s", (total, order_id))
            
            if (i + 1) % 1000 == 0:
                logger.info(f"  Created {i + 1}/{count} orders...")
        
        logger.info(f"Seeded {count} orders")
    finally:
        await cursor.close()


async def seed_reviews(conn, count=5000):
    logger.info(f"Seeding {count} reviews...")
    cursor = await conn.cursor()
    
    try:
        await cursor.execute("SELECT id FROM demo_users")
        user_ids = [r[0] for r in await cursor.fetchall()]
        
        await cursor.execute("SELECT id FROM demo_products")
        product_ids = [r[0] for r in await cursor.fetchall()]
        
        adjectives = ["great", "okay", "bad", "amazing", "not worth it", "excellent", "terrible"]
        
        reviews = []
        for _ in range(count):
            reviews.append((
                random.choice(product_ids),
                random.choice(user_ids),
                random.randint(1, 5),
                f"This product is {random.choice(adjectives)}. " * random.randint(1, 10),
                random.choice([True, False]),
                random.randint(0, 100)
            ))
        
        await cursor.executemany("""
            INSERT INTO demo_reviews (product_id, user_id, rating, comment, is_verified, helpful_votes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, reviews)
        
        logger.info(f"Seeded {count} reviews")
    finally:
        await cursor.close()


async def seed_activity(conn, count=100000):
    logger.info(f"Seeding {count} activity logs (this may take a while)...")
    cursor = await conn.cursor()
    
    try:
        await cursor.execute("SELECT id FROM demo_users")
        user_ids = [r[0] for r in await cursor.fetchall()]
        
        activity_types = ['page_view', 'click', 'add_to_cart', 'search', 'filter', 'checkout']
        
        batch_size = 5000
        for batch_start in range(0, count, batch_size):
            activities = []
            batch_end = min(batch_start + batch_size, count)
            
            for _ in range(batch_end - batch_start):
                activities.append((
                    random.choice(user_ids),
                    f"sess_{random.getrandbits(32)}",
                    random.choice(activity_types),
                    f"/product/{random.randint(1, 1000)}",
                    json.dumps({"browser": "Chrome", "os": "Linux"}),
                    f"192.168.1.{random.randint(1, 254)}"
                ))
            
            await cursor.executemany("""
                INSERT INTO demo_user_activity (user_id, session_id, activity_type, path, metadata, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, activities)
            
            logger.info(f"  Inserted {batch_end}/{count} activity logs...")
        
        logger.info(f"Seeded {count} activity logs")
    finally:
        await cursor.close()


async def create_bottlenecks(conn):
    """Intentionally create performance issues."""
    logger.info("Creating intentional performance bottlenecks...")
    cursor = await conn.cursor()
    
    try:
        # 1. Create index bloat scenario by many updates
        logger.info("  Creating index on inventory for bloat test...")
        await cursor.execute("CREATE INDEX idx_inventory_qty ON demo_inventory(quantity)")
        
        logger.info("  Running multiple updates to cause index fragmentation...")
        for _ in range(5):
            await cursor.execute("UPDATE demo_inventory SET quantity = quantity + 1")
        
        # 2. Run slow queries to populate performance_schema
        logger.info("  Executing slow queries to populate performance_schema...")
        
        slow_queries = [
            # Sequential scan on large table (no index on activity_type)
            "SELECT COUNT(*) FROM demo_user_activity WHERE activity_type = 'search'",
            
            # Join without optimal indexes
            "SELECT u.username, o.total_amount FROM demo_users u JOIN demo_orders o ON u.id = o.user_id WHERE u.email LIKE '%user_1%' LIMIT 100",
            
            # Complex aggregation with function on column
            "SELECT DATE(created_at), SUM(total_amount) FROM demo_orders GROUP BY DATE(created_at) ORDER BY 1 DESC LIMIT 30",
            
            # Cross join (partial)
            "SELECT COUNT(*) FROM demo_products p1, demo_products p2 WHERE p1.category = p2.category AND p1.id < p2.id LIMIT 1000",
            
            # JSON operations without virtual column index
            "SELECT username FROM demo_users WHERE JSON_EXTRACT(profile_data, '$.city') = 'Berlin' LIMIT 100",
        ]
        
        for i, query in enumerate(slow_queries):
            try:
                await cursor.execute(query)
                await cursor.fetchall()
                logger.info(f"    Executed slow query {i + 1}/{len(slow_queries)}")
            except Exception as e:
                logger.warning(f"    Query {i + 1} failed (expected): {e}")
        
        logger.info("Performance bottlenecks created")
        
    finally:
        await cursor.close()


async def main():
    logger.info("=" * 60)
    logger.info("Starting COMPLEX Demo Data Seeding for MySQLens")
    logger.info("=" * 60)
    
    config = get_database_config()
    
    try:
        conn = await aiomysql.connect(**config)
        logger.info("Connected to MySQL")
        
        await setup_schema(conn)
        
        cursor = await conn.cursor()
        await cursor.execute("USE mysqlens_complex")
        await cursor.close()
        
        await seed_users(conn)
        await seed_products(conn)
        await seed_inventory(conn)
        await seed_coupons(conn)
        await seed_orders(conn)
        await seed_reviews(conn)
        await seed_activity(conn)
        
        await create_bottlenecks(conn)
        
        # Get summary
        cursor = await conn.cursor()
        await cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM demo_users) as users,
                (SELECT COUNT(*) FROM demo_products) as products,
                (SELECT COUNT(*) FROM demo_orders) as orders,
                (SELECT COUNT(*) FROM demo_user_activity) as activities
        """)
        summary = await cursor.fetchone()
        await cursor.close()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Complex Demo Data Seeding Completed!")
        logger.info("=" * 60)
        logger.info(f"  Users: {summary[0]}")
        logger.info(f"  Products: {summary[1]}")
        logger.info(f"  Orders: {summary[2]}")
        logger.info(f"  Activity Logs: {summary[3]}")
        logger.info("")
        logger.info("Bottlenecks created:")
        logger.info("  - Missing indexes on demo_orders.user_id")
        logger.info("  - Missing indexes on demo_user_activity.activity_type")
        logger.info("  - JSON queries without virtual column indexes")
        logger.info("  - Index fragmentation on demo_inventory")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    asyncio.run(main())
