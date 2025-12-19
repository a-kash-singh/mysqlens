"""
Settings router for MySQLens.
"""

import logging
from fastapi import APIRouter
from config import settings
from llm.factory import llm_factory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/llm-providers")
async def get_llm_providers():
    """Get available LLM providers."""
    available = llm_factory.get_available_providers()
    return {
        "success": True,
        "data": {
            "available": available,
            "current": settings.llm_provider
        }
    }


@router.get("/config")
async def get_configuration():
    """Get current configuration (non-sensitive)."""
    return {
        "success": True,
        "data": {
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "llm_provider": settings.llm_provider,
            "polling_interval": settings.polling_interval,
            "top_queries_limit": settings.top_queries_limit
        }
    }

