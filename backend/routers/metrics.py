"""
Metrics router for MySQLens.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from models import APIResponse
from services.metric_service import metric_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/queries")
async def get_query_metrics(
    limit: int = Query(default=50, ge=10, le=500),
    include_system: bool = Query(default=False)
):
    """Get query metrics from performance_schema."""
    try:
        result = await metric_service.fetch_query_metrics(
            sample_size=limit,
            include_system_queries=include_system
        )
        
        return APIResponse(
            success=True,
            message="Query metrics retrieved",
            data={
                "metrics": result["metrics"],
                "total_count": result["total_count"],
                "sample_size": len(result["metrics"])
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch query metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vitals")
async def get_vitals():
    """Get database vitals (QPS, buffer pool, connections)."""
    try:
        vitals = await metric_service.fetch_vitals()
        
        return APIResponse(
            success=True,
            message="Vitals retrieved",
            data=vitals
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch vitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db-info")
async def get_database_info():
    """Get database information."""
    try:
        db_info = await metric_service.fetch_db_info()
        
        if "error" in db_info:
            raise HTTPException(status_code=500, detail=db_info["error"])
        
        return APIResponse(
            success=True,
            message="Database info retrieved",
            data=db_info
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_performance_schema():
    """Reset performance_schema statistics."""
    try:
        success = await metric_service.reset_stats()
        
        if success:
            return APIResponse(
                success=True,
                message="Performance schema statistics reset",
                data=None
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to reset statistics")
            
    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
