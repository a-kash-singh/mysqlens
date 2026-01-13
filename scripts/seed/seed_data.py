#!/usr/bin/env python3
"""
MySQLens Demo Data Seeder
Creates realistic MySQL database with performance bottlenecks for demo purposes.
Adapted for MySQL from OptiSchema's PostgreSQL version.
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

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


def get_database_config():
    """Get database configuration from environment or config file."""
    # Try environment variables first
    host = os.getenv('MYSQL_HOST', os.getenv('DB_HOST', 'localhost'))
    port = int(os.getenv('MYSQL_PORT', os.getenv('DB_PORT', '3306')))
    user = os.getenv('MYSQL_USER', os.getenv('DB_USER', 'root'))
    password = os.getenv('MYSQL_PASSWORD', os.getenv('DB_PASSWORD', ''))
    database = os.getenv('MYSQL_DATABASE', os.getenv('DB_NAME', 'mysqlens_demo'))
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'db': database,
        'autocommit': True,
        'charset': 'utf8mb4'
    }


async def create_demo_schema(conn):
    """Create demo tables with realistic structure."""
    cursor = await conn.cursor()
    
    try:
        # Create demo database if not exists
        await cursor.execute("CREATE DATABASE IF NOT EXISTS mysqlens_demo")
        await cursor.execute("USE mysqlens_demo")
        
        # Drop existing tables
        await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        tables = ['demo_order_items', 'demo_orders', 'demo_users', 'demo_products', 'demo_logs']
        for table in tables:
            await cursor.execute(f"DROP TABLE IF EXISTS {table}")
        await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Create users table
        await cursor.execute("""
            CREATE TABLE demo_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE,
                profile_data JSON
            ) ENGINE=InnoDB
        """)
        
        # Create orders table (intentionally NO index on user_id for bottleneck)
        await cursor.execute("""
            CREATE TABLE demo_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                shipping_address TEXT,
                billing_address TEXT
            ) ENGINE=InnoDB
        """)
        
        # Create products table
        await cursor.execute("""
            CREATE TABLE demo_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(100),
                stock_quantity INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)
        
        # Create order_items table (NO index on order_id or product_id for bottleneck)
        await cursor.execute("""
            CREATE TABLE demo_order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL
            ) ENGINE=InnoDB
        """)
        
        # Create logs table (large table without proper indexes)
        await cursor.execute("""
            CREATE TABLE demo_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action VARCHAR(50) NOT NULL,
                details JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB
        """)
        
        logger.info("Demo schema created successfully")
        
    finally:
        await cursor.close()


async def seed_users(conn, count=1000):
    """Seed users with realistic data."""
    logger.info(f"Seeding {count} users...")
    cursor = await conn.cursor()
    
    try:
        users_data = []
        for i in range(count):
            username = f"user{i:04d}"
            email = f"user{i:04d}@example.com"
            is_active = random.choice([True, False])
            profile = json.dumps({
                "age": random.randint(18, 80),
                "location": random.choice(["US", "UK", "CA", "AU", "DE", "FR", "JP"]),
                "preferences": {
                    "theme": random.choice(["light", "dark"]),
                    "notifications": random.choice([True, False])
                }
            })
            users_data.append((username, email, is_active, profile))
        
        await cursor.executemany("""
            INSERT INTO demo_users (username, email, is_active, profile_data)
            VALUES (%s, %s, %s, %s)
        """, users_data)
        
        logger.info(f"Seeded {count} users")
        
    finally:
        await cursor.close()


async def seed_products(conn, count=500):
    """Seed products with realistic data."""
    logger.info(f"Seeding {count} products...")
    cursor = await conn.cursor()
    
    try:
        categories = ["Electronics", "Clothing", "Books", "Home", "Sports", "Food", "Beauty", "Toys"]
        
        products_data = []
        for i in range(count):
            name = f"Product {i:04d}"
            description = f"This is a description for product {i:04d}. High quality item with great features."
            price = round(random.uniform(10.0, 1000.0), 2)
            category = random.choice(categories)
            stock = random.randint(0, 1000)
            products_data.append((name, description, price, category, stock))
        
        await cursor.executemany("""
            INSERT INTO demo_products (name, description, price, category, stock_quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, products_data)
        
        logger.info(f"Seeded {count} products")
        
    finally:
        await cursor.close()


async def seed_orders(conn, count=5000):
    """Seed orders with realistic data."""
    logger.info(f"Seeding {count} orders...")
    cursor = await conn.cursor()
    
    try:
        # Get user IDs
        await cursor.execute("SELECT id FROM demo_users")
        user_ids = [row[0] for row in await cursor.fetchall()]
        
        # Get product info
        await cursor.execute("SELECT id, price FROM demo_products")
        products = {row[0]: row[1] for row in await cursor.fetchall()}
        product_ids = list(products.keys())
        
        statuses = ['pending', 'processing', 'shipped', 'completed', 'cancelled']
        
        for i in range(count):
            user_id = random.choice(user_ids)
            days_ago = random.randint(0, 365)
            order_date = datetime.now() - timedelta(days=days_ago)
            status = random.choice(statuses)
            
            # Insert order
            await cursor.execute("""
                INSERT INTO demo_orders (user_id, order_date, total_amount, status, shipping_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, order_date, 0, status, f"{random.randint(1, 999)} Main Street, City, ST 12345"))
            
            order_id = cursor.lastrowid
            
            # Add 1-5 items to each order
            num_items = random.randint(1, 5)
            total_amount = 0
            order_items = []
            
            for _ in range(num_items):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 10)
                unit_price = float(products[product_id])
                order_items.append((order_id, product_id, quantity, unit_price))
                total_amount += quantity * unit_price
            
            # Insert order items
            await cursor.executemany("""
                INSERT INTO demo_order_items (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, order_items)
            
            # Update order total
            await cursor.execute(
                "UPDATE demo_orders SET total_amount = %s WHERE id = %s",
                (total_amount, order_id)
            )
            
            if (i + 1) % 500 == 0:
                logger.info(f"  Created {i + 1}/{count} orders...")
        
        logger.info(f"Seeded {count} orders with items")
        
    finally:
        await cursor.close()


async def seed_logs(conn, count=50000):
    """Seed logs with realistic data (creates performance bottlenecks)."""
    logger.info(f"Seeding {count} log entries...")
    cursor = await conn.cursor()
    
    try:
        # Get user IDs
        await cursor.execute("SELECT id FROM demo_users")
        user_ids = [row[0] for row in await cursor.fetchall()]
        
        actions = ["login", "logout", "view_product", "add_to_cart", "purchase", "search", "profile_update"]
        browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
        
        batch_size = 1000
        for batch_start in range(0, count, batch_size):
            logs_data = []
            batch_end = min(batch_start + batch_size, count)
            
            for _ in range(batch_end - batch_start):
                user_id = random.choice(user_ids) if random.random() > 0.1 else None
                action = random.choice(actions)
                details = json.dumps({
                    "page": f"/page/{random.randint(1, 100)}",
                    "session_id": f"session_{random.randint(1000, 9999)}",
                    "browser": random.choice(browsers),
                    "referrer": random.choice([None, "google.com", "facebook.com", "twitter.com"])
                })
                ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.randint(500, 600)}.{random.randint(1, 50)}"
                days_ago = random.randint(0, 30)
                created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                logs_data.append((user_id, action, details, ip, user_agent, created_at))
            
            await cursor.executemany("""
                INSERT INTO demo_logs (user_id, action, details, ip_address, user_agent, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, logs_data)
            
            logger.info(f"  Inserted {batch_end}/{count} logs...")
        
        logger.info(f"Seeded {count} log entries")
        
    finally:
        await cursor.close()


async def create_performance_bottlenecks(conn):
    """Execute queries that will show up as slow in performance_schema."""
    logger.info("Creating performance bottlenecks...")
    cursor = await conn.cursor()
    
    try:
        # 1. Slow query - no index on user_id in orders
        logger.info("  Running slow query 1: Unindexed JOIN...")
        await cursor.execute("""
            SELECT u.username, COUNT(o.id) as order_count, SUM(o.total_amount) as total_spent
            FROM demo_users u
            LEFT JOIN demo_orders o ON u.id = o.user_id
            WHERE u.created_at > DATE_SUB(NOW(), INTERVAL 1 YEAR)
            GROUP BY u.id, u.username
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        await cursor.fetchall()
        
        # 2. Slow query - subquery in SELECT
        logger.info("  Running slow query 2: Correlated subquery...")
        await cursor.execute("""
            SELECT o.id, o.order_date, o.total_amount,
                   (SELECT username FROM demo_users WHERE id = o.user_id) as username
            FROM demo_orders o
            WHERE o.order_date > DATE_SUB(NOW(), INTERVAL 1 YEAR)
            LIMIT 100
        """)
        await cursor.fetchall()
        
        # 3. Slow query - LIKE on unindexed column
        logger.info("  Running slow query 3: LIKE on unindexed column...")
        await cursor.execute("""
            SELECT * FROM demo_products 
            WHERE description LIKE '%electronics%' 
            OR description LIKE '%digital%'
            OR description LIKE '%smart%'
        """)
        await cursor.fetchall()
        
        # 4. Slow query - Complex aggregation
        logger.info("  Running slow query 4: Complex aggregation...")
        await cursor.execute("""
            SELECT 
                DATE(o.order_date) as day,
                COUNT(*) as orders,
                SUM(o.total_amount) as revenue,
                AVG(o.total_amount) as avg_order_value
            FROM demo_orders o
            JOIN demo_users u ON o.user_id = u.id
            WHERE o.order_date > DATE_SUB(NOW(), INTERVAL 1 YEAR)
            AND u.is_active = 1
            GROUP BY DATE(o.order_date)
            ORDER BY day DESC
        """)
        await cursor.fetchall()
        
        # 5. Slow query - JSON operations
        logger.info("  Running slow query 5: JSON operations...")
        await cursor.execute("""
            SELECT username, JSON_UNQUOTE(JSON_EXTRACT(profile_data, '$.location')) as location
            FROM demo_users
            WHERE JSON_UNQUOTE(JSON_EXTRACT(profile_data, '$.location')) = 'US'
            AND JSON_UNQUOTE(JSON_EXTRACT(profile_data, '$.preferences.theme')) = 'dark'
        """)
        await cursor.fetchall()
        
        logger.info("Performance bottleneck queries executed")
        
    finally:
        await cursor.close()


async def main():
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Starting MySQLens Demo Data Seeding")
    logger.info("=" * 60)
    
    config = get_database_config()
    logger.info(f"Connecting to MySQL at {config['host']}:{config['port']}")
    
    try:
        # Connect to MySQL
        conn = await aiomysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            autocommit=True,
            charset='utf8mb4'
        )
        
        logger.info("Connected to MySQL")
        
        # Create schema
        await create_demo_schema(conn)
        
        # Use the demo database
        cursor = await conn.cursor()
        await cursor.execute("USE mysqlens_demo")
        await cursor.close()
        
        # Seed data
        await seed_users(conn, 1000)
        await seed_products(conn, 500)
        await seed_orders(conn, 5000)
        await seed_logs(conn, 50000)
        
        # Create performance bottlenecks
        await create_performance_bottlenecks(conn)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Demo Data Seeding Completed!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Demo Data Summary:")
        logger.info("  - 1,000 users")
        logger.info("  - 500 products")
        logger.info("  - 5,000 orders with ~15,000 order items")
        logger.info("  - 50,000 log entries")
        logger.info("  - Performance bottlenecks created for demo")
        logger.info("")
        logger.info("Your MySQLens dashboard should now show meaningful data!")
        logger.info("Visit: http://localhost:3000/dashboard")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    asyncio.run(main())
