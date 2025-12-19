"""
Metric Service for MySQLens.
Fetches query metrics from performance_schema.
"""

import logging
from typing import List, Dict, Any, Optional
from connection_manager import connection_manager
import aiomysql

logger = logging.getLogger(__name__)


class MetricService:
    """Service for collecting metrics from MySQL performance_schema."""
    
    async def fetch_query_metrics(
        self,
        sample_size: int = 50,
        include_system_queries: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch query metrics from performance_schema.events_statements_summary_by_digest.
        
        Args:
            sample_size: Number of top queries to fetch (default 50)
            include_system_queries: Include system/internal queries
            
        Returns:
            Dict with 'metrics' (list) and 'total_count' (int)
        """
        pool = await connection_manager.get_pool()
        if not pool:
            logger.warning("No active database connection")
            return {"metrics": [], "total_count": 0}
        
        # Clamp sample_size to sane limits
        sample_size = max(10, min(sample_size, 500))
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Check if performance_schema is enabled
                    await cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM information_schema.SCHEMATA
                        WHERE SCHEMA_NAME = 'performance_schema'
                    """)
                    result = await cursor.fetchone()
                    
                    if not result or result['count'] == 0:
                        logger.warning("performance_schema is not enabled")
                        return {"metrics": [], "total_count": 0}
                    
                    # Build WHERE clause
                    where_conditions = ["DIGEST IS NOT NULL"]
                    if not include_system_queries:
                        where_conditions.extend([
                            "AND DIGEST_TEXT NOT LIKE 'EXPLAIN%'",
                            "AND DIGEST_TEXT NOT LIKE 'SHOW%'",
                            "AND DIGEST_TEXT NOT LIKE 'SET %'",
                            "AND DIGEST_TEXT NOT LIKE 'SELECT @@%'",
                            "AND SCHEMA_NAME NOT IN ('performance_schema', 'information_schema', 'mysql', 'sys')"
                        ])
                    
                    where_clause = " ".join(where_conditions)
                    
                    # Get total count
                    count_query = f"""
                        SELECT COUNT(*) as total
                        FROM performance_schema.events_statements_summary_by_digest
                        WHERE {where_clause}
                    """
                    await cursor.execute(count_query)
                    count_result = await cursor.fetchone()
                    total_count = count_result['total'] if count_result else 0
                    
                    # Fetch sampled metrics
                    query = f"""
                        SELECT
                            DIGEST as digest,
                            DIGEST_TEXT as digest_text,
                            SCHEMA_NAME as schema_name,
                            COUNT_STAR as count_star,
                            SUM_TIMER_WAIT as sum_timer_wait,
                            AVG_TIMER_WAIT as avg_timer_wait,
                            MIN_TIMER_WAIT as min_timer_wait,
                            MAX_TIMER_WAIT as max_timer_wait,
                            SUM_LOCK_TIME as sum_lock_time,
                            SUM_ROWS_EXAMINED as sum_rows_examined,
                            SUM_ROWS_SENT as sum_rows_sent,
                            SUM_ROWS_AFFECTED as sum_rows_affected,
                            SUM_CREATED_TMP_TABLES as sum_created_tmp_tables,
                            SUM_CREATED_TMP_DISK_TABLES as sum_created_tmp_disk_tables,
                            SUM_SELECT_SCAN as sum_select_scan,
                            SUM_SELECT_FULL_JOIN as sum_select_full_join,
                            SUM_NO_INDEX_USED as sum_no_index_used,
                            SUM_NO_GOOD_INDEX_USED as sum_no_good_index_used
                        FROM performance_schema.events_statements_summary_by_digest
                        WHERE {where_clause}
                        ORDER BY SUM_TIMER_WAIT DESC
                        LIMIT {sample_size}
                    """
                    
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    
                    # Convert picoseconds to milliseconds for readability
                    metrics = []
                    for row in rows:
                        metrics.append({
                            "digest": row['digest'],
                            "digest_text": row['digest_text'][:1000] if row['digest_text'] else "",
                            "schema_name": row['schema_name'],
                            "count_star": row['count_star'],
                            "sum_timer_wait_ms": row['sum_timer_wait'] / 1_000_000_000 if row['sum_timer_wait'] else 0,
                            "avg_timer_wait_ms": row['avg_timer_wait'] / 1_000_000_000 if row['avg_timer_wait'] else 0,
                            "min_timer_wait_ms": row['min_timer_wait'] / 1_000_000_000 if row['min_timer_wait'] else 0,
                            "max_timer_wait_ms": row['max_timer_wait'] / 1_000_000_000 if row['max_timer_wait'] else 0,
                            "sum_lock_time_ms": row['sum_lock_time'] / 1_000_000_000 if row['sum_lock_time'] else 0,
                            "sum_rows_examined": row['sum_rows_examined'],
                            "sum_rows_sent": row['sum_rows_sent'],
                            "sum_rows_affected": row['sum_rows_affected'],
                            "sum_created_tmp_tables": row['sum_created_tmp_tables'],
                            "sum_created_tmp_disk_tables": row['sum_created_tmp_disk_tables'],
                            "sum_select_scan": row['sum_select_scan'],
                            "sum_select_full_join": row['sum_select_full_join'],
                            "sum_no_index_used": row['sum_no_index_used'],
                            "sum_no_good_index_used": row['sum_no_good_index_used']
                        })
                    
                    return {
                        "metrics": metrics,
                        "total_count": total_count
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return {"metrics": [], "total_count": 0}
    
    async def fetch_vitals(self) -> Dict[str, Any]:
        """
        Fetch database vitals: QPS, Buffer Pool, Active Connections.
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return {
                "qps": {"value": 0.0, "status": "disabled"},
                "buffer_pool_hit_ratio": {"value": None, "status": "disabled"},
                "active_connections": {"value": 0, "status": "disabled"},
                "max_connections": {"value": 0, "status": "disabled"},
                "error": "No database connection"
            }
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get buffer pool hit ratio from performance_schema
                    await cursor.execute("""
                        SELECT
                            VARIABLE_VALUE
                        FROM performance_schema.global_status
                        WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
                    """)
                    read_requests = await cursor.fetchone()
                    
                    await cursor.execute("""
                        SELECT VARIABLE_VALUE
                        FROM performance_schema.global_status
                        WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
                    """)
                    disk_reads = await cursor.fetchone()
                    
                    buffer_hit_ratio = None
                    if read_requests and disk_reads:
                        total_reads = int(read_requests['VARIABLE_VALUE'])
                        disk = int(disk_reads['VARIABLE_VALUE'])
                        if total_reads > 0:
                            buffer_hit_ratio = round(((total_reads - disk) / total_reads) * 100, 2)
                    
                    # Get connections
                    await cursor.execute("""
                        SELECT
                            (SELECT COUNT(*) FROM performance_schema.threads WHERE TYPE = 'FOREGROUND') as active,
                            (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') as max_conn
                    """)
                    connections = await cursor.fetchone()
                    
                    # Calculate QPS from performance_schema
                    await cursor.execute("""
                        SELECT
                            SUM(COUNT_STAR) as total_queries
                        FROM performance_schema.events_statements_summary_by_digest
                    """)
                    query_result = await cursor.fetchone()
                    
                    # Get uptime for QPS calculation
                    await cursor.execute("""
                        SELECT VARIABLE_VALUE
                        FROM performance_schema.global_status
                        WHERE VARIABLE_NAME = 'Uptime'
                    """)
                    uptime_result = await cursor.fetchone()
                    
                    qps_value = 0.0
                    if query_result and uptime_result:
                        total_queries = int(query_result['total_queries'] or 0)
                        uptime = int(uptime_result['VARIABLE_VALUE'] or 1)
                        if uptime > 0:
                            qps_value = round(total_queries / uptime, 2)
                    
                    return {
                        "qps": {"value": qps_value, "status": "ok"},
                        "buffer_pool_hit_ratio": {
                            "value": buffer_hit_ratio,
                            "status": "ok" if buffer_hit_ratio is not None else "insufficient_data"
                        },
                        "active_connections": {
                            "value": int(connections['active']) if connections else 0,
                            "status": "ok"
                        },
                        "max_connections": {
                            "value": int(connections['max_conn']) if connections else 0,
                            "status": "ok"
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching vitals: {e}")
            return {
                "qps": {"value": 0.0, "status": "error"},
                "buffer_pool_hit_ratio": {"value": None, "status": "error"},
                "active_connections": {"value": 0, "status": "error"},
                "max_connections": {"value": 0, "status": "error"},
                "error": str(e)
            }
    
    async def fetch_db_info(self) -> Dict[str, Any]:
        """
        Fetch database information: version, engines, size, etc.
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return {"error": "No database connection"}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get MySQL version
                    await cursor.execute("SELECT VERSION() as version")
                    version_result = await cursor.fetchone()
                    version = version_result['version'] if version_result else "Unknown"
                    
                    # Get current database
                    await cursor.execute("SELECT DATABASE() as db_name")
                    db_result = await cursor.fetchone()
                    db_name = db_result['db_name'] if db_result else "Unknown"
                    
                    # Get database size
                    await cursor.execute("""
                        SELECT
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                        FROM information_schema.TABLES
                        WHERE table_schema = DATABASE()
                    """)
                    size_result = await cursor.fetchone()
                    db_size_mb = size_result['size_mb'] if size_result else 0
                    
                    # Get table count
                    await cursor.execute("""
                        SELECT COUNT(*) as table_count
                        FROM information_schema.TABLES
                        WHERE table_schema = DATABASE()
                        AND table_type = 'BASE TABLE'
                    """)
                    table_result = await cursor.fetchone()
                    table_count = table_result['table_count'] if table_result else 0
                    
                    # Get storage engines
                    await cursor.execute("""
                        SELECT
                            ENGINE,
                            COUNT(*) as count
                        FROM information_schema.TABLES
                        WHERE table_schema = DATABASE()
                        GROUP BY ENGINE
                    """)
                    engines = await cursor.fetchall()
                    
                    return {
                        "version": version,
                        "database_name": db_name,
                        "database_size_mb": db_size_mb,
                        "database_size": f"{db_size_mb} MB",
                        "table_count": table_count,
                        "storage_engines": [
                            {"engine": e['ENGINE'], "count": e['count']}
                            for e in engines
                        ],
                        "has_performance_schema": True,  # We already checked in fetch_query_metrics
                        "has_sys_schema": await self._check_sys_schema(cursor)
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching DB info: {e}")
            return {"error": str(e)}
    
    async def _check_sys_schema(self, cursor) -> bool:
        """Check if sys schema is available."""
        try:
            await cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME = 'sys'
            """)
            result = await cursor.fetchone()
            return result['count'] > 0 if result else False
        except Exception:
            return False
    
    async def reset_stats(self) -> bool:
        """
        Reset performance_schema statistics.
        Returns True if successful, False otherwise.
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return False
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        TRUNCATE TABLE performance_schema.events_statements_summary_by_digest
                    """)
                    return True
        except Exception as e:
            logger.error(f"Error resetting stats: {e}")
            return False


# Global service instance
metric_service = MetricService()
