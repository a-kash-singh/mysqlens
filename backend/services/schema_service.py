"""
Schema Service for MySQLens.
Fetches table definitions, indexes, and statistics.
"""

import logging
from typing import List, Dict, Any, Optional
from connection_manager import connection_manager

logger = logging.getLogger(__name__)


class SchemaService:
    """Service for fetching MySQL schema information."""
    
    async def get_all_tables(self, schema_name: Optional[str] = None) -> List[str]:
        """List all tables in the current database or specified schema."""
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if not schema_name:
                        # Get current database
                        await cursor.execute("SELECT DATABASE()")
                        result = await cursor.fetchone()
                        schema_name = result[0] if result else None
                    
                    if not schema_name:
                        return []
                    
                    await cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (schema_name,))
                    
                    rows = await cursor.fetchall()
                    return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    async def get_table_info(self, table_name: str, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """Get table columns, indexes, and row count estimate."""
        pool = await connection_manager.get_pool()
        if not pool:
            return {}
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if not schema_name:
                        # Get current database
                        await cursor.execute("SELECT DATABASE()")
                        result = await cursor.fetchone()
                        schema_name = result[0] if result else None
                    
                    if not schema_name:
                        return {}
                    
                    # Get columns
                    await cursor.execute("""
                        SELECT 
                            column_name,
                            column_type,
                            is_nullable,
                            column_key,
                            extra
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (schema_name, table_name))
                    
                    column_rows = await cursor.fetchall()
                    columns = []
                    for row in column_rows:
                        columns.append({
                            'column_name': row[0],
                            'data_type': row[1],
                            'is_nullable': row[2],
                            'column_key': row[3],
                            'extra': row[4]
                        })
                    
                    # Get indexes
                    await cursor.execute("""
                        SELECT 
                            index_name,
                            column_name,
                            index_type,
                            non_unique,
                            seq_in_index
                        FROM information_schema.statistics
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY index_name, seq_in_index
                    """, (schema_name, table_name))
                    
                    index_rows = await cursor.fetchall()
                    
                    # Group indexes by name
                    indexes_dict = {}
                    for row in index_rows:
                        index_name = row[0]
                        if index_name not in indexes_dict:
                            indexes_dict[index_name] = {
                                'index_name': index_name,
                                'columns': [],
                                'index_type': row[2],
                                'is_unique': row[3] == 0
                            }
                        indexes_dict[index_name]['columns'].append(row[1])
                    
                    indexes = list(indexes_dict.values())
                    
                    # Get row count estimate
                    await cursor.execute("""
                        SELECT table_rows
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    """, (schema_name, table_name))
                    
                    row_count_result = await cursor.fetchone()
                    row_count = row_count_result[0] if row_count_result else 0
                    
                    # Get table size
                    await cursor.execute("""
                        SELECT 
                            ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                            ROUND(data_length / 1024 / 1024, 2) AS data_size_mb,
                            ROUND(index_length / 1024 / 1024, 2) AS index_size_mb
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    """, (schema_name, table_name))
                    
                    size_result = await cursor.fetchone()
                    table_size = {
                        'total_mb': size_result[0] if size_result else 0,
                        'data_mb': size_result[1] if size_result and len(size_result) > 1 else 0,
                        'index_mb': size_result[2] if size_result and len(size_result) > 2 else 0
                    }
                    
                    return {
                        "table_name": table_name,
                        "schema_name": schema_name,
                        "columns": columns,
                        "indexes": indexes,
                        "row_count": row_count,
                        "size": table_size
                    }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {}
    
    async def get_context_for_query(self, table_names: List[str]) -> str:
        """
        Get rich context for a list of tables.
        Returns a formatted string for the LLM.
        """
        context_parts = []
        
        for table in table_names:
            info = await self.get_table_info(table)
            if not info:
                continue
            
            # Format columns
            columns_str = ", ".join([
                f"{c['column_name']} ({c['data_type']})" 
                for c in info.get('columns', [])
            ])
            
            # Format indexes
            indexes_list = []
            for idx in info.get('indexes', []):
                unique_str = "UNIQUE " if idx.get('is_unique') else ""
                cols = ", ".join(idx.get('columns', []))
                indexes_list.append(f"{unique_str}{idx['index_name']} ({cols})")
            indexes_str = ", ".join(indexes_list) if indexes_list else "No indexes"
            
            # Format row count and size
            row_count = info.get('row_count', 0)
            size_info = info.get('size', {})
            size_str = f"{size_info.get('total_mb', 0)} MB"
            
            context_parts.append(f"""
Table: {table} ({row_count:,} rows, {size_str})
Columns: {columns_str}
Indexes: {indexes_str}
""")
        
        return "\n".join(context_parts)
    
    async def get_index_usage_stats(self) -> List[Dict[str, Any]]:
        """Get index usage statistics from performance_schema."""
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check if performance_schema is enabled
                    await cursor.execute("SELECT @@performance_schema")
                    perf_schema = await cursor.fetchone()
                    
                    if not perf_schema or perf_schema[0] != 1:
                        return []
                    
                    # Get current database
                    await cursor.execute("SELECT DATABASE()")
                    db_result = await cursor.fetchone()
                    db_name = db_result[0] if db_result else None
                    
                    if not db_name:
                        return []
                    
                    # Get index usage stats
                    await cursor.execute("""
                        SELECT 
                            t.table_name,
                            s.index_name,
                            s.count_star AS usage_count,
                            s.sum_timer_wait / 1000000000000 AS total_latency_sec
                        FROM performance_schema.table_io_waits_summary_by_index_usage s
                        JOIN information_schema.tables t 
                            ON s.object_schema = t.table_schema 
                            AND s.object_name = t.table_name
                        WHERE s.object_schema = %s
                            AND s.index_name IS NOT NULL
                        ORDER BY s.count_star DESC
                    """, (db_name,))
                    
                    rows = await cursor.fetchall()
                    stats = []
                    for row in rows:
                        stats.append({
                            'table_name': row[0],
                            'index_name': row[1],
                            'usage_count': row[2],
                            'total_latency_sec': float(row[3]) if row[3] else 0
                        })
                    
                    return stats
        except Exception as e:
            logger.error(f"Error getting index usage stats: {e}")
            return []
    
    async def get_unused_indexes(self, min_size_mb: float = 1.0) -> List[Dict[str, Any]]:
        """Find potentially unused indexes."""
        pool = await connection_manager.get_pool()
        if not pool:
            return []
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Get current database
                    await cursor.execute("SELECT DATABASE()")
                    db_result = await cursor.fetchone()
                    db_name = db_result[0] if db_result else None
                    
                    if not db_name:
                        return []
                    
                    # Find indexes with no usage
                    await cursor.execute("""
                        SELECT 
                            t.table_name,
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
                        GROUP BY t.table_name, s.index_name
                        HAVING size_mb >= %s
                        ORDER BY size_mb DESC
                    """, (db_name, min_size_mb))
                    
                    rows = await cursor.fetchall()
                    unused = []
                    for row in rows:
                        unused.append({
                            'table_name': row[0],
                            'index_name': row[1],
                            'size_mb': float(row[2])
                        })
                    
                    return unused
        except Exception as e:
            logger.error(f"Error finding unused indexes: {e}")
            return []


schema_service = SchemaService()

