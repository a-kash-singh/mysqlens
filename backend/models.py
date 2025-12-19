"""
Pydantic models for MySQLens backend.
Defines data structures for query metrics, analysis results, and recommendations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class QueryMetrics(BaseModel):
    """Model for MySQL query metrics from performance_schema."""
    
    tenant_id: UUID = Field(..., description="Tenant identifier")
    digest: str = Field(..., description="Query digest hash")
    digest_text: str = Field(..., description="Normalized query text")
    count_star: int = Field(..., description="Number of times executed")
    sum_timer_wait: int = Field(..., description="Total execution time (picoseconds)")
    avg_timer_wait: float = Field(..., description="Average execution time (picoseconds)")
    min_timer_wait: Optional[int] = Field(None, description="Minimum execution time")
    max_timer_wait: Optional[int] = Field(None, description="Maximum execution time")
    sum_lock_time: Optional[int] = Field(None, description="Total lock time")
    sum_rows_examined: Optional[int] = Field(None, description="Total rows examined")
    sum_rows_sent: Optional[int] = Field(None, description="Total rows sent")
    sum_rows_affected: Optional[int] = Field(None, description="Total rows affected")
    sum_created_tmp_tables: Optional[int] = Field(None, description="Temporary tables created")
    sum_created_tmp_disk_tables: Optional[int] = Field(None, description="Disk temp tables created")
    performance_score: Optional[int] = Field(None, ge=0, le=100, description="Performance score (0-100)")
    time_percentage: Optional[float] = Field(None, description="Percentage of total database time")
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionPlan(BaseModel):
    """Model for MySQL EXPLAIN plan analysis."""
    
    plan_json: Dict[str, Any] = Field(..., description="Raw EXPLAIN JSON")
    query_cost: Optional[float] = Field(None, description="Total query cost")
    rows_examined: Optional[int] = Field(None, description="Estimated rows examined")
    full_table_scans: int = Field(default=0, description="Number of full table scans")
    using_filesort: bool = Field(default=False, description="Whether filesort is used")
    using_temp_table: bool = Field(default=False, description="Whether temp table is used")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Plan nodes")


class AnalysisResult(BaseModel):
    """Model for query analysis results."""
    
    tenant_id: UUID = Field(..., description="Tenant identifier")
    id: Optional[UUID] = Field(None, description="Unique identifier")
    digest: str = Field(..., description="Query digest")
    digest_text: str = Field(..., description="Query text")
    execution_plan: Optional[ExecutionPlan] = Field(None, description="Execution plan analysis")
    analysis_summary: Optional[str] = Field(None, description="AI-generated analysis summary")
    performance_score: Optional[int] = Field(None, ge=0, le=100, description="Performance score (0-100)")
    bottleneck_type: Optional[str] = Field(None, description="Type of performance bottleneck")
    bottleneck_details: Optional[Dict[str, Any]] = Field(None, description="Detailed bottleneck information")
    created_at: Optional[datetime] = Field(None, description="Analysis timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class Recommendation(BaseModel):
    """Model for optimization recommendations."""
    
    tenant_id: UUID = Field(..., description="Tenant identifier")
    id: Optional[UUID] = Field(None, description="Unique identifier")
    digest: str = Field(..., description="Query digest")
    recommendation_type: str = Field(..., description="Type of recommendation (index, rewrite, config)")
    title: str = Field(..., description="Short title for the recommendation")
    description: str = Field(..., description="Detailed description of the recommendation")
    sql_fix: Optional[str] = Field(None, description="SQL to apply the fix")
    original_sql: Optional[str] = Field(None, description="Original query SQL")
    optimized_sql: Optional[str] = Field(None, description="Optimized query SQL")
    estimated_improvement_percent: Optional[int] = Field(None, ge=0, le=100, description="Estimated improvement percentage")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Confidence in the recommendation (0-100)")
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")
    status: str = Field(default="pending", description="Status (pending, active, applied, dismissed)")
    applied: bool = Field(default=False, description="Whether the recommendation has been applied")
    applied_at: Optional[datetime] = Field(None, description="When the recommendation was applied")
    created_at: Optional[datetime] = Field(None, description="Recommendation creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheck(BaseModel):
    """Model for health check response."""
    
    status: str = Field(..., description="Health status (healthy, unhealthy)")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: bool = Field(..., description="Database connection status")
    llm: bool = Field(..., description="LLM API status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Application uptime in seconds")


class ConnectionConfig(BaseModel):
    """Model for database connection configuration."""
    
    host: str = Field(..., description="Database host")
    port: int = Field(default=3306, description="Database port")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    database: str = Field(..., description="Database name")
    ssl: bool = Field(default=False, description="Use SSL/TLS")


class ConnectionStatus(BaseModel):
    """Model for connection status response."""
    
    connected: bool = Field(..., description="Whether connected to database")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    version: Optional[str] = Field(None, description="MySQL version")
    user: Optional[str] = Field(None, description="Database user")


class IndexRecommendation(BaseModel):
    """Model for index recommendations."""
    
    tenant_id: UUID = Field(..., description="Tenant identifier")
    id: Optional[UUID] = Field(None, description="Unique identifier")
    index_name: str = Field(..., description="Name of the index")
    table_name: str = Field(..., description="Name of the table")
    schema_name: str = Field(..., description="Name of the schema")
    index_type: str = Field(..., description="Type (unused, redundant, missing)")
    columns: List[str] = Field(..., description="Index columns")
    size_mb: Optional[float] = Field(None, description="Index size in MB")
    recommendation: str = Field(..., description="Recommendation text")
    sql_fix: Optional[str] = Field(None, description="SQL to fix issue")
    risk_level: str = Field(..., description="Risk level (low, medium, high)")
    estimated_savings_mb: Optional[float] = Field(None, description="Estimated savings in MB")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class HealthScanResult(BaseModel):
    """Model for database health scan results."""
    
    scan_timestamp: str = Field(..., description="When the scan was performed")
    health_score: int = Field(..., ge=0, le=100, description="Overall health score (0-100)")
    buffer_pool_health: Dict[str, Any] = Field(..., description="InnoDB buffer pool check results")
    table_issues: Dict[str, Any] = Field(..., description="Table fragmentation and issues")
    index_issues: Dict[str, Any] = Field(..., description="Index usage and redundancy")
    config_issues: Dict[str, Any] = Field(..., description="Configuration recommendations")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    error: Optional[str] = Field(None, description="Error message if scan failed")


class MetricsSummary(BaseModel):
    """Model for aggregated metrics summary."""
    
    total_queries: int = Field(..., description="Total number of unique queries")
    total_execution_time: float = Field(..., description="Total execution time (seconds)")
    average_query_time: float = Field(..., description="Average execution time (seconds)")
    qps: float = Field(..., description="Queries per second")
    cache_hit_ratio: Optional[float] = Field(None, description="Buffer pool cache hit ratio")
    active_connections: int = Field(..., description="Active connections")
    max_connections: int = Field(..., description="Max connections configured")
    last_updated: datetime = Field(..., description="Last metrics update timestamp")


# API Response models
class APIResponse(BaseModel):
    """Base model for API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
