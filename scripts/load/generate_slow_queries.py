#!/usr/bin/env python3
"""
Generate intentionally slow queries to test MySQLens UI performance indicators.
Creates temporary large tables and runs complex queries.
"""

import asyncio
import aiomysql
import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'db': os.getenv('MYSQL_DATABASE', 'mysqlens_demo'),
    'autocommit': True,
    'charset': 'utf8mb4'
}


async def create_temp_table(cursor):
    """Create a large temporary table for slow queries."""
    logger.info("Creating large temporary table...")
    
    # Drop if exists
    await cursor.execute("DROP TABLE IF EXISTS temp_slow_query_test")
    
    # Create table
    await cursor.execute("""
        CREATE TABLE temp_slow_query_test (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(255),
            value DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    
    # Insert data in batches
    logger.info("Inserting 100,000 rows...")
    batch_size = 10000
    for batch in range(10):
        values = []
        for i in range(batch_size):
            row_id = batch * batch_size + i
            values.append(f"('data_{row_id}', {row_id * 0.001})")
        
        await cursor.execute(f"""
            INSERT INTO temp_slow_query_test (data, value) VALUES {','.join(values)}
        """)
        logger.info(f"  Inserted batch {batch + 1}/10...")
    
    logger.info("✅ Temporary table created with 100,000 rows")


async def generate_slow_queries(cursor):
    """Generate intentionally slow queries."""
    logger.info("\n🐌 Running slow queries...")
    
    slow_queries = [
        # Cross join - creates cartesian product
        (
            "Cross JOIN (cartesian product)",
            """
            SELECT a.id, b.id, a.data, b.data 
            FROM temp_slow_query_test a, temp_slow_query_test b 
            WHERE a.value > b.value
            LIMIT 1000
            """
        ),
        
        # Complex aggregation without indexes
        (
            "Complex aggregation",
            """
            SELECT 
                SUBSTRING(data, 1, 10) as prefix,
                COUNT(*) as cnt,
                AVG(value) as avg_val,
                SUM(value) as sum_val,
                MIN(value) as min_val,
                MAX(value) as max_val,
                STDDEV(value) as std_val
            FROM temp_slow_query_test 
            GROUP BY prefix
            ORDER BY cnt DESC 
            LIMIT 100
            """
        ),
        
        # Multiple subqueries
        (
            "Multiple subqueries",
            """
            SELECT * FROM temp_slow_query_test t1
            WHERE id IN (
                SELECT id FROM temp_slow_query_test WHERE value > 0.5
            ) 
            AND id IN (
                SELECT id FROM temp_slow_query_test WHERE data LIKE '%1%'
            )
            AND value > (SELECT AVG(value) FROM temp_slow_query_test)
            LIMIT 1000
            """
        ),
        
        # Window functions simulation (MySQL 8.0+)
        (
            "User variables for ranking",
            """
            SELECT 
                t.id,
                t.data,
                t.value,
                @row_num := @row_num + 1 as row_num,
                @running_sum := @running_sum + t.value as running_sum
            FROM temp_slow_query_test t, (SELECT @row_num := 0, @running_sum := 0) vars
            ORDER BY t.value DESC
            LIMIT 1000
            """
        ),
        
        # Complex text operations
        (
            "Complex string operations",
            """
            SELECT 
                id,
                data,
                value,
                LENGTH(data) as data_length,
                UPPER(data) as upper_data,
                LOWER(data) as lower_data,
                REVERSE(data) as reversed,
                CONCAT(data, '_suffix') as concatenated
            FROM temp_slow_query_test 
            WHERE data LIKE '%1%' 
            OR data LIKE '%2%' 
            OR data LIKE '%3%'
            ORDER BY data_length DESC 
            LIMIT 1000
            """
        ),
        
        # Self-join with inequality
        (
            "Self-join with inequality",
            """
            SELECT t1.id, t2.id, ABS(t1.value - t2.value) as diff
            FROM temp_slow_query_test t1
            JOIN temp_slow_query_test t2 ON t1.id != t2.id AND ABS(t1.value - t2.value) < 0.001
            LIMIT 1000
            """
        ),
    ]
    
    for i, (name, query) in enumerate(slow_queries):
        logger.info(f"\nRunning slow query {i+1}/{len(slow_queries)}: {name}")
        
        # Run each query multiple times to build up statistics
        for run in range(3):
            try:
                start_time = time.time()
                await cursor.execute(query)
                await cursor.fetchall()
                elapsed = time.time() - start_time
                logger.info(f"  Run {run + 1}: {elapsed:.2f} seconds")
            except Exception as e:
                logger.error(f"  Run {run + 1} failed: {e}")
    
    logger.info("\n✅ Slow query generation completed!")


async def cleanup(cursor):
    """Clean up temporary table."""
    logger.info("\n🧹 Cleaning up...")
    await cursor.execute("DROP TABLE IF EXISTS temp_slow_query_test")
    logger.info("✅ Cleanup complete")


async def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("MySQLens Slow Query Generator")
    logger.info("=" * 60)
    logger.info(f"Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}")
    
    conn = None
    
    try:
        # Connect to database
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        
        logger.info("✅ Connected to MySQL")
        
        # Create temporary table
        await create_temp_table(cursor)
        
        # Generate slow queries
        await generate_slow_queries(cursor)
        
        # Cleanup
        await cleanup(cursor)
        
        await cursor.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 Slow queries generated!")
        logger.info("Check your MySQLens dashboard for slow query indicators.")
        logger.info("Visit: http://localhost:3000/dashboard")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    asyncio.run(main())
