"""
Health Scan Service for MySQLens.
Performs database health checks and identifies issues.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from connection_manager import connection_manager

logger = logging.getLogger(__name__)


class HealthScanService:
    """Service for database health scanning."""
    
    async def perform_health_scan(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health scan of the database.
        
        Returns:
            Dictionary with health scan results
        """
        try:
            table_stats = await self._check_table_stats()
            index_usage = await self._check_index_usage()
            config_issues = await self._check_config()
            
            # Calculate health score (0-100)
            health_score = self._calculate_health_score(table_stats, index_usage, config_issues)
            
            return {
                "scan_timestamp": datetime.utcnow().isoformat(),
                "health_score": health_score,
                "table_stats": table_stats,
                "index_usage": index_usage,
                "config_issues": config_issues,
                "summary": {
                    "total_issues": (
                        len(table_stats.get('issues', [])) +
                        len(index_usage.get('issues', [])) +
                        len(config_issues.get('issues', []))
                    ),
                    "critical_issues": sum(
                        1 for issue in (
                            table_stats.get('issues', []) +
                            index_usage.get('issues', []) +
                            config_issues.get('issues', [])
                        )
                        if issue.get('severity') == 'high'
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing health scan: {e}")
            return {
                "scan_timestamp": datetime.utcnow().isoformat(),
                "health_score": 0,
                "error": str(e)
            }
    
    async def _check_table_stats(self) -> Dict[str, Any]:
        """Check table statistics and identify issues."""
        pool = await connection_manager.get_pool()
        if not pool:
            return {"issues": [], "status": "no_connection"}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE()")
                    db_result = await cursor.fetchone()
                    db_name = db_result[0] if db_result else None
                    
                    if not db_name:
                        return {"issues": [], "status": "no_database"}
                    
                    # Check for tables without primary keys
                    await cursor.execute("""
                        SELECT 
                            t.table_name,
                            t.table_rows,
                            ROUND((t.data_length + t.index_length) / 1024 / 1024, 2) AS size_mb
                        FROM information_schema.tables t
                        LEFT JOIN information_schema.key_column_usage k 
                            ON t.table_schema = k.table_schema 
                            AND t.table_name = k.table_name 
                            AND k.constraint_name = 'PRIMARY'
                        WHERE t.table_schema = %s
                            AND t.table_type = 'BASE TABLE'
                            AND k.constraint_name IS NULL
                            AND t.table_rows > 100
                    """, (db_name,))
                    
                    tables_no_pk = await cursor.fetchall()
                    
                    issues = []
                    for row in tables_no_pk:
                        issues.append({
                            "table": row[0],
                            "severity": "high",
                            "issue": "No primary key",
                            "recommendation": f"Add a primary key to table {row[0]} for better performance and data integrity"
                        })
                    
                    # Check for large tables
                    await cursor.execute("""
                        SELECT 
                            table_name,
                            table_rows,
                            ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
                        FROM information_schema.tables
                        WHERE table_schema = %s
                            AND table_type = 'BASE TABLE'
                            AND (data_length + index_length) > 1073741824
                        ORDER BY (data_length + index_length) DESC
                    """, (db_name,))
                    
                    large_tables = await cursor.fetchall()
                    
                    for row in large_tables:
                        issues.append({
                            "table": row[0],
                            "severity": "medium",
                            "issue": f"Large table ({row[2]} MB)",
                            "recommendation": "Consider partitioning or archiving old data"
                        })
                    
                    return {
                        "issues": issues,
                        "status": "ok",
                        "tables_without_pk": len(tables_no_pk),
                        "large_tables": len(large_tables)
                    }
                    
        except Exception as e:
            logger.error(f"Error checking table stats: {e}")
            return {"issues": [], "status": "error", "error": str(e)}
    
    async def _check_index_usage(self) -> Dict[str, Any]:
        """Check index usage and identify unused indexes."""
        pool = await connection_manager.get_pool()
        if not pool:
            return {"issues": [], "status": "no_connection"}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE()")
                    db_result = await cursor.fetchone()
                    db_name = db_result[0] if db_result else None
                    
                    if not db_name:
                        return {"issues": [], "status": "no_database"}
                    
                    # Check performance_schema availability
                    await cursor.execute("SELECT @@performance_schema")
                    perf_schema = await cursor.fetchone()
                    
                    if not perf_schema or perf_schema[0] != 1:
                        return {"issues": [], "status": "performance_schema_disabled"}
                    
                    # Find potentially unused indexes
                    await cursor.execute("""
                        SELECT 
                            s.table_name,
                            s.index_name,
                            ROUND(stat.index_length / 1024 / 1024, 2) AS size_mb
                        FROM information_schema.statistics s
                        JOIN information_schema.tables stat 
                            ON s.table_schema = stat.table_schema 
                            AND s.table_name = stat.table_name
                        LEFT JOIN performance_schema.table_io_waits_summary_by_index_usage u
                            ON s.table_schema = u.object_schema 
                            AND s.table_name = u.object_name 
                            AND s.index_name = u.index_name
                        WHERE s.table_schema = %s
                            AND s.index_name != 'PRIMARY'
                            AND (u.count_star = 0 OR u.count_star IS NULL)
                            AND stat.index_length > 1048576
                        GROUP BY s.table_name, s.index_name
                        ORDER BY size_mb DESC
                    """, (db_name,))
                    
                    unused_indexes = await cursor.fetchall()
                    
                    issues = []
                    for row in unused_indexes:
                        issues.append({
                            "table": row[0],
                            "index": row[1],
                            "size_mb": float(row[2]),
                            "severity": "medium",
                            "issue": "Unused index",
                            "recommendation": f"Consider dropping unused index {row[1]} to save {row[2]} MB"
                        })
                    
                    return {
                        "issues": issues,
                        "status": "ok",
                        "unused_indexes": len(unused_indexes)
                    }
                    
        except Exception as e:
            logger.error(f"Error checking index usage: {e}")
            return {"issues": [], "status": "error", "error": str(e)}
    
    async def _check_config(self) -> Dict[str, Any]:
        """Check MySQL configuration for potential issues."""
        pool = await connection_manager.get_pool()
        if not pool:
            return {"issues": [], "status": "no_connection"}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check important configuration variables
                    await cursor.execute("""
                        SELECT 
                            variable_name,
                            variable_value
                        FROM performance_schema.global_variables
                        WHERE variable_name IN (
                            'max_connections',
                            'innodb_buffer_pool_size',
                            'query_cache_size',
                            'tmp_table_size',
                            'max_heap_table_size',
                            'innodb_log_file_size'
                        )
                    """)
                    
                    config_vars = await cursor.fetchall()
                    config_dict = {row[0]: row[1] for row in config_vars}
                    
                    issues = []
                    
                    # Check buffer pool size
                    buffer_pool = int(config_dict.get('innodb_buffer_pool_size', 0))
                    if buffer_pool < 134217728:  # 128MB
                        issues.append({
                            "setting": "innodb_buffer_pool_size",
                            "current_value": f"{buffer_pool / 1024 / 1024:.0f} MB",
                            "severity": "high",
                            "issue": "InnoDB buffer pool too small",
                            "recommendation": "Increase innodb_buffer_pool_size to at least 512MB or 70% of available RAM"
                        })
                    
                    # Check temp table sizes
                    tmp_table = int(config_dict.get('tmp_table_size', 0))
                    if tmp_table < 16777216:  # 16MB
                        issues.append({
                            "setting": "tmp_table_size",
                            "current_value": f"{tmp_table / 1024 / 1024:.0f} MB",
                            "severity": "medium",
                            "issue": "Temporary table size too small",
                            "recommendation": "Increase tmp_table_size to at least 64MB"
                        })
                    
                    return {
                        "issues": issues,
                        "status": "ok",
                        "config_values": config_dict
                    }
                    
        except Exception as e:
            logger.error(f"Error checking config: {e}")
            return {"issues": [], "status": "error", "error": str(e)}
    
    def _calculate_health_score(
        self,
        table_stats: Dict[str, Any],
        index_usage: Dict[str, Any],
        config_issues: Dict[str, Any]
    ) -> int:
        """Calculate overall health score (0-100)."""
        score = 100
        
        # Deduct points for issues
        for issue in table_stats.get('issues', []):
            if issue.get('severity') == 'high':
                score -= 15
            elif issue.get('severity') == 'medium':
                score -= 10
            else:
                score -= 5
        
        for issue in index_usage.get('issues', []):
            if issue.get('severity') == 'high':
                score -= 10
            elif issue.get('severity') == 'medium':
                score -= 5
        
        for issue in config_issues.get('issues', []):
            if issue.get('severity') == 'high':
                score -= 15
            elif issue.get('severity') == 'medium':
                score -= 10
        
        return max(0, min(100, score))


health_scan_service = HealthScanService()

