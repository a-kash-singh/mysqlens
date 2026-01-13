#!/usr/bin/env python3
"""
MySQL Load Generator for MySQLens
Runs intentionally slow/inefficient queries to generate realistic workload
that will show up in performance_schema for analysis.
"""

import asyncio
import aiomysql
import os
import sys
import random
import signal
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'db': os.getenv('MYSQL_DATABASE', 'mysqlens_demo'),
    'autocommit': True,
    'charset': 'utf8mb4'
}

# Control flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    global running
    logger.info("\n🛑 Shutting down load generator...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def run_slow_queries(conn):
    """Run a set of intentionally slow/inefficient queries."""
    cursor = await conn.cursor()
    
    try:
        # 1. Unindexed scan on logs
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Unindexed scan on demo_logs...")
        await cursor.execute("""
            SELECT action, COUNT(*) as cnt
            FROM demo_logs 
            WHERE user_agent LIKE '%Mozilla%' 
            AND created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY action
            ORDER BY cnt DESC
        """)
        await cursor.fetchall()

        # 2. Inefficient JOIN without proper indexes
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Large JOIN without indexes...")
        await cursor.execute("""
            SELECT u.username, o.total_amount, oi.quantity, p.name
            FROM demo_users u
            JOIN demo_orders o ON u.id = o.user_id
            JOIN demo_order_items oi ON o.id = oi.order_id
            JOIN demo_products p ON oi.product_id = p.id
            WHERE o.total_amount > 500
            ORDER BY o.total_amount DESC
            LIMIT 100
        """)
        await cursor.fetchall()

        # 3. Complex JSON search on unindexed field
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Slow JSON search...")
        await cursor.execute("""
            SELECT username, JSON_UNQUOTE(JSON_EXTRACT(profile_data, '$.preferences.theme')) as theme
            FROM demo_users
            WHERE JSON_UNQUOTE(JSON_EXTRACT(profile_data, '$.location')) = 'US'
            AND JSON_EXTRACT(profile_data, '$.age') > 30
        """)
        await cursor.fetchall()

        # 4. Aggregation on large dataset without covering index
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Heavy aggregation...")
        await cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00') as hour,
                action,
                COUNT(*) as count
            FROM demo_logs
            GROUP BY hour, action
            ORDER BY count DESC
            LIMIT 50
        """)
        await cursor.fetchall()

        # 5. Correlated subquery (N+1 pattern)
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Correlated subquery...")
        await cursor.execute("""
            SELECT 
                o.id,
                o.total_amount,
                (SELECT COUNT(*) FROM demo_order_items WHERE order_id = o.id) as item_count,
                (SELECT username FROM demo_users WHERE id = o.user_id) as customer
            FROM demo_orders o
            WHERE o.order_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY o.total_amount DESC
            LIMIT 50
        """)
        await cursor.fetchall()

        # 6. LIKE with leading wildcard (cannot use index)
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: LIKE with leading wildcard...")
        await cursor.execute("""
            SELECT * FROM demo_products 
            WHERE description LIKE '%electronics%'
            OR name LIKE '%premium%'
            LIMIT 100
        """)
        await cursor.fetchall()

        # 7. Cross join with filter (expensive)
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Expensive cross join...")
        await cursor.execute("""
            SELECT COUNT(*) 
            FROM demo_products p1, demo_products p2 
            WHERE p1.category = p2.category 
            AND p1.id < p2.id
            AND p1.price > p2.price
        """)
        await cursor.fetchall()

        # 8. ORDER BY on unindexed columns
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: Expensive ORDER BY...")
        await cursor.execute("""
            SELECT * FROM demo_orders
            WHERE status = 'pending'
            ORDER BY total_amount DESC, order_date ASC
            LIMIT 100
        """)
        await cursor.fetchall()

    finally:
        await cursor.close()


async def run_random_queries(conn):
    """Run random variations of queries."""
    cursor = await conn.cursor()
    
    try:
        query_templates = [
            "SELECT * FROM demo_users WHERE email LIKE '%{pattern}%' LIMIT 10",
            "SELECT COUNT(*) FROM demo_orders WHERE total_amount > {amount}",
            "SELECT * FROM demo_logs WHERE action = '{action}' ORDER BY created_at DESC LIMIT 100",
            "SELECT AVG(total_amount), MAX(total_amount) FROM demo_orders WHERE user_id = {user_id}",
            "SELECT p.name, COUNT(oi.id) FROM demo_products p LEFT JOIN demo_order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY COUNT(oi.id) DESC LIMIT 20",
        ]
        
        patterns = ["user", "admin", "test", "demo", "example"]
        actions = ["login", "logout", "view_product", "add_to_cart", "purchase"]
        
        query = random.choice(query_templates)
        query = query.format(
            pattern=random.choice(patterns),
            amount=random.randint(100, 1000),
            action=random.choice(actions),
            user_id=random.randint(1, 1000)
        )
        
        await cursor.execute(query)
        await cursor.fetchall()
        
    finally:
        await cursor.close()


async def main():
    """Main load generator loop."""
    global running
    
    logger.info("🚀 Starting MySQL Load Generator for MySQLens")
    logger.info(f"   Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}")
    logger.info("   Press Ctrl+C to stop")
    logger.info("")
    
    # Wait for DB to be ready
    retry_count = 0
    conn = None
    
    while retry_count < 10 and running:
        try:
            conn = await aiomysql.connect(**DB_CONFIG)
            
            # Verify tables exist
            cursor = await conn.cursor()
            await cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'demo_logs'
            """, (DB_CONFIG['db'],))
            result = await cursor.fetchone()
            await cursor.close()
            
            if result and result[0] > 0:
                logger.info("✅ Connected to database, tables found")
                break
            else:
                logger.info("⏳ Waiting for tables to be seeded...")
                conn.close()
                conn = None
                
        except Exception as e:
            logger.warning(f"⏳ Waiting for database... ({e})")
        
        await asyncio.sleep(5)
        retry_count += 1
    
    if not conn:
        logger.error("❌ Could not connect to database. Exiting.")
        return
    
    # Main loop
    iteration = 0
    try:
        while running:
            iteration += 1
            logger.info(f"\n{'='*50}")
            logger.info(f"Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*50}")
            
            try:
                # Run slow queries
                await run_slow_queries(conn)
                
                # Run some random queries
                for _ in range(random.randint(3, 8)):
                    await run_random_queries(conn)
                
                logger.info(f"✅ Iteration {iteration} complete")
                
                # Random sleep between iterations
                wait_time = random.uniform(2, 10)
                logger.info(f"💤 Sleeping for {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"⚠️ Error in iteration: {e}")
                await asyncio.sleep(5)
                
                # Try to reconnect
                try:
                    conn = await aiomysql.connect(**DB_CONFIG)
                except Exception:
                    pass
                    
    finally:
        if conn:
            conn.close()
        logger.info("👋 Load generator stopped")


if __name__ == "__main__":
    asyncio.run(main())
