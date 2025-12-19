"""
Index Advisor Service for MySQLens.
Analyzes index usage and provides recommendations.
"""

import logging
from typing import List, Dict, Any
from connection_manager import connection_manager
import aiomysql

logger = logging.getLogger(__name__)


class IndexAdvisorService:
    """Service for analyzing indexes and providing recommendations."""
    
    async def analyze_unused_indexes(self, min_size_mb: float = 1.0) -> List[Dict[str, Any]]:
        """
        Find unused indexes that are taking up space.
        
        Args:
            min_size_mb: Minimum index size to report (default 1MB)
            
        Returns:
            List of unused index recommendations
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE() as db_name")
                    db_result = await cursor.fetchone()
                    db_name = db_result['db_name'] if db_result else None
                    
                    if not db_name:
                        return []
                    
                    # Find indexes with no usage from performance_schema
                    await cursor.execute("""
                        SELECT 
                            s.table_name,
                            s.index_name,
                            ROUND(stat.index_length / 1024 / 1024, 2) AS size_mb,
                            s.cardinality
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
                            AND stat.index_length > %s
                        GROUP BY s.table_name, s.index_name, stat.index_length, s.cardinality
                        ORDER BY size_mb DESC
                    """, (db_name, min_size_mb * 1024 * 1024))
                    
                    rows = await cursor.fetchall()
                    
                    recommendations = []
                    for row in rows:
                        recommendations.append({
                            "type": "unused_index",
                            "table": row['table_name'],
                            "index": row['index_name'],
                            "size_mb": float(row['size_mb']),
                            "cardinality": row['cardinality'],
                            "recommendation": f"Drop unused index {row['index_name']} on table {row['table_name']} to save {row['size_mb']} MB",
                            "sql": f"DROP INDEX {row['index_name']} ON {row['table_name']};",
                            "risk_level": "low"
                        })
                    
                    return recommendations
                    
        except Exception as e:
            logger.error(f"Error analyzing unused indexes: {e}")
            return []
    
    async def analyze_redundant_indexes(self) -> List[Dict[str, Any]]:
        """
        Find redundant/duplicate indexes.
        
        Returns:
            List of redundant index recommendations
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE() as db_name")
                    db_result = await cursor.fetchone()
                    db_name = db_result['db_name'] if db_result else None
                    
                    if not db_name:
                        return []
                    
                    # Get all indexes grouped by table
                    await cursor.execute("""
                        SELECT 
                            table_name,
                            index_name,
                            GROUP_CONCAT(column_name ORDER BY seq_in_index) as columns,
                            non_unique
                        FROM information_schema.statistics
                        WHERE table_schema = %s
                            AND index_name != 'PRIMARY'
                        GROUP BY table_name, index_name, non_unique
                        ORDER BY table_name, index_name
                    """, (db_name,))
                    
                    indexes = await cursor.fetchall()
                    
                    # Find redundant indexes
                    recommendations = []
                    checked = set()
                    
                    for i, idx1 in enumerate(indexes):
                        for idx2 in indexes[i+1:]:
                            if idx1['table_name'] != idx2['table_name']:
                                continue
                            
                            key = (idx1['table_name'], idx1['index_name'], idx2['index_name'])
                            if key in checked:
                                continue
                            checked.add(key)
                            
                            cols1 = idx1['columns'].split(',')
                            cols2 = idx2['columns'].split(',')
                            
                            # Check if one index is a prefix of another
                            if cols1 == cols2[:len(cols1)] or cols2 == cols1[:len(cols2)]:
                                redundant_idx = idx1['index_name'] if len(cols1) < len(cols2) else idx2['index_name']
                                recommendations.append({
                                    "type": "redundant_index",
                                    "table": idx1['table_name'],
                                    "index": redundant_idx,
                                    "redundant_with": idx2['index_name'] if redundant_idx == idx1['index_name'] else idx1['index_name'],
                                    "recommendation": f"Index {redundant_idx} is redundant with {idx2['index_name'] if redundant_idx == idx1['index_name'] else idx1['index_name']}",
                                    "sql": f"DROP INDEX {redundant_idx} ON {idx1['table_name']};",
                                    "risk_level": "medium"
                                })
                    
                    return recommendations
                    
        except Exception as e:
            logger.error(f"Error analyzing redundant indexes: {e}")
            return []
    
    async def analyze_missing_indexes(self) -> List[Dict[str, Any]]:
        """
        Suggest missing indexes based on query patterns.
        
        Returns:
            List of missing index recommendations
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Find queries with full table scans or no good index used
                    await cursor.execute("""
                        SELECT 
                            DIGEST_TEXT as query,
                            COUNT_STAR as executions,
                            SUM_NO_INDEX_USED as no_index_count,
                            SUM_NO_GOOD_INDEX_USED as no_good_index_count,
                            ROUND(SUM_TIMER_WAIT / 1000000000, 2) as total_time_ms
                        FROM performance_schema.events_statements_summary_by_digest
                        WHERE DIGEST_TEXT IS NOT NULL
                            AND (SUM_NO_INDEX_USED > 0 OR SUM_NO_GOOD_INDEX_USED > 0)
                            AND DIGEST_TEXT NOT LIKE 'SHOW%'
                            AND DIGEST_TEXT NOT LIKE 'SET%'
                        ORDER BY SUM_NO_INDEX_USED DESC, COUNT_STAR DESC
                        LIMIT 20
                    """)
                    
                    rows = await cursor.fetchall()
                    
                    recommendations = []
                    for row in rows:
                        if row['no_index_count'] and row['no_index_count'] > 0:
                            recommendations.append({
                                "type": "missing_index",
                                "query": row['query'][:200] + "..." if len(row['query']) > 200 else row['query'],
                                "executions": row['executions'],
                                "no_index_used": row['no_index_count'],
                                "total_time_ms": float(row['total_time_ms']),
                                "recommendation": "Query is executing without using any index. Consider adding an index on WHERE/JOIN columns.",
                                "severity": "high",
                                "risk_level": "low"
                            })
                    
                    return recommendations
                    
        except Exception as e:
            logger.error(f"Error analyzing missing indexes: {e}")
            return []
    
    async def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive index analysis.
        
        Returns:
            Dictionary with all analysis results
        """
        try:
            unused = await self.analyze_unused_indexes()
            redundant = await self.analyze_redundant_indexes()
            missing = await self.analyze_missing_indexes()
            
            total_wasted_space = sum(idx.get('size_mb', 0) for idx in unused)
            
            return {
                "success": True,
                "summary": {
                    "unused_indexes": len(unused),
                    "redundant_indexes": len(redundant),
                    "missing_indexes": len(missing),
                    "total_wasted_space_mb": round(total_wasted_space, 2)
                },
                "unused": unused,
                "redundant": redundant,
                "missing": missing
            }
            
        except Exception as e:
            logger.error(f"Error running full analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_database_index_stats(self) -> Dict[str, Any]:
        """
        Get overall database index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        pool = await connection_manager.get_pool()
        if not pool:
            return {"error": "No database connection"}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE() as db_name")
                    db_result = await cursor.fetchone()
                    db_name = db_result['db_name'] if db_result else None
                    
                    if not db_name:
                        return {"error": "No database selected"}
                    
                    # Get index statistics
                    await cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT s.table_name) as total_tables,
                            COUNT(DISTINCT s.index_name) as total_indexes,
                            ROUND(SUM(stat.index_length) / 1024 / 1024, 2) as total_index_size_mb
                        FROM information_schema.statistics s
                        JOIN information_schema.tables stat
                            ON s.table_schema = stat.table_schema
                            AND s.table_name = stat.table_name
                        WHERE s.table_schema = %s
                    """, (db_name,))
                    
                    stats = await cursor.fetchone()
                    
                    # Get index usage summary
                    await cursor.execute("""
                        SELECT 
                            COUNT(*) as tracked_indexes,
                            SUM(CASE WHEN count_star = 0 THEN 1 ELSE 0 END) as unused_indexes
                        FROM performance_schema.table_io_waits_summary_by_index_usage
                        WHERE object_schema = %s
                            AND index_name IS NOT NULL
                            AND index_name != 'PRIMARY'
                    """, (db_name,))
                    
                    usage = await cursor.fetchone()
                    
                    return {
                        "database": db_name,
                        "total_tables": stats['total_tables'],
                        "total_indexes": stats['total_indexes'],
                        "total_index_size_mb": float(stats['total_index_size_mb']),
                        "tracked_indexes": usage['tracked_indexes'] if usage else 0,
                        "unused_indexes": usage['unused_indexes'] if usage else 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}


# Global service instance
index_advisor_service = IndexAdvisorService()
