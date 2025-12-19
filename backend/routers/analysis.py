"""
Analysis router for MySQLens.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import APIResponse
from services.index_advisor import index_advisor_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/indexes/unused")
async def get_unused_indexes():
    """Get unused index recommendations."""
    try:
        recommendations = await index_advisor_service.analyze_unused_indexes()
        
        return APIResponse(
            success=True,
            message=f"Found {len(recommendations)} unused indexes",
            data={"recommendations": recommendations}
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze unused indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexes/redundant")
async def get_redundant_indexes():
    """Get redundant index recommendations."""
    try:
        recommendations = await index_advisor_service.analyze_redundant_indexes()
        
        return APIResponse(
            success=True,
            message=f"Found {len(recommendations)} redundant indexes",
            data={"recommendations": recommendations}
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze redundant indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexes/missing")
async def get_missing_indexes():
    """Get missing index recommendations."""
    try:
        recommendations = await index_advisor_service.analyze_missing_indexes()
        
        return APIResponse(
            success=True,
            message=f"Found {len(recommendations)} potential index opportunities",
            data={"recommendations": recommendations}
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze missing indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexes/full")
async def run_full_index_analysis():
    """Run comprehensive index analysis."""
    try:
        result = await index_advisor_service.run_full_analysis()
        
        if result.get("success"):
            return APIResponse(
                success=True,
                message="Index analysis completed",
                data=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
            
    except Exception as e:
        logger.error(f"Failed to run full index analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexes/stats")
async def get_index_stats():
    """Get database index statistics."""
    try:
        stats = await index_advisor_service.get_database_index_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return APIResponse(
            success=True,
            message="Index statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
