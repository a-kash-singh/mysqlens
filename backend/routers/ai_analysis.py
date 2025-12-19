"""
AI Analysis router for MySQLens.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import APIResponse
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryAnalysisRequest(BaseModel):
    """Request model for query analysis."""
    query_text: str
    include_schema: bool = False


@router.post("/analyze")
async def analyze_query(request: QueryAnalysisRequest):
    """Analyze a query using AI."""
    try:
        result = await llm_service.analyze_query(
            query_text=request.query_text,
            execution_plan=None,
            metrics=None,
            schema_context=None if not request.include_schema else "Schema context placeholder"
        )
        
        if result.get("success"):
            return APIResponse(
                success=True,
                message="AI analysis completed",
                data=result
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
            
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
