"""
Health router for MySQLens.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import APIResponse
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scan")
async def run_health_scan():
    """Run database health scan."""
    try:
        # Placeholder for health scan service
        # TODO: Implement comprehensive health scan
        
        return APIResponse(
            success=True,
            message="Health scan feature coming soon",
            data={
                "scan_timestamp": "2024-01-01T00:00:00",
                "health_score": 85,
                "summary": "Database is healthy"
            }
        )
        
    except Exception as e:
        logger.error(f"Health scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama")
async def check_ollama_health():
    """
    Check Ollama service health and configuration.

    Returns detailed information about Ollama availability,
    configured model, and available models.
    """
    try:
        if settings.llm_provider != "ollama":
            return APIResponse(
                success=True,
                message="Ollama is not the active LLM provider",
                data={
                    "active_provider": settings.llm_provider,
                    "ollama_configured": False
                }
            )

        # Import here to avoid circular dependencies
        from llm.ollama_provider import OllamaProvider

        provider = OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )

        health_info = await provider.health_check()

        return APIResponse(
            success=health_info["healthy"],
            message="Ollama health check complete" if health_info["healthy"] else "Ollama is not healthy",
            data=health_info
        )

    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return APIResponse(
            success=False,
            message="Failed to check Ollama health",
            data={
                "error": str(e),
                "suggestions": [
                    "Ensure Ollama is installed and running",
                    "Run: ./install-ollama.sh for automated setup"
                ]
            }
        )


@router.get("/ollama/models")
async def get_ollama_models():
    """
    Get list of available Ollama models.

    Useful for checking which models are installed
    and can be used for analysis.
    """
    try:
        if settings.llm_provider != "ollama":
            return APIResponse(
                success=False,
                message="Ollama is not the active LLM provider",
                data={
                    "active_provider": settings.llm_provider
                }
            )

        from llm.ollama_provider import OllamaProvider

        provider = OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )

        models_info = await provider.get_available_models()

        return APIResponse(
            success=models_info["success"],
            message="Retrieved Ollama models" if models_info["success"] else "Failed to get models",
            data=models_info
        )

    except Exception as e:
        logger.error(f"Failed to get Ollama models: {e}")
        return APIResponse(
            success=False,
            message="Failed to retrieve Ollama models",
            data={"error": str(e)}
        )


@router.get("/llm")
async def check_llm_provider():
    """
    Check the active LLM provider and its configuration.

    Returns information about which LLM provider is active,
    whether it's properly configured, and privacy status.
    """
    try:
        provider_info = {
            "active_provider": settings.llm_provider,
            "local_mode": settings.llm_provider == "ollama",
            "privacy_mode": settings.llm_provider == "ollama",
            "zero_data_egress": settings.llm_provider == "ollama",
            "configured": False,
            "details": {}
        }

        if settings.llm_provider == "ollama":
            provider_info["configured"] = bool(settings.ollama_base_url and settings.ollama_model)
            provider_info["details"] = {
                "base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "privacy_benefits": [
                    "All data stays on localhost",
                    "Zero API costs",
                    "Works offline",
                    "GDPR/HIPAA friendly"
                ]
            }
        elif settings.llm_provider == "openai":
            provider_info["configured"] = bool(settings.openai_api_key)
            provider_info["details"] = {
                "model": getattr(settings, "openai_model", "gpt-4o"),
                "note": "Data sent to OpenAI API"
            }
        elif settings.llm_provider == "gemini":
            provider_info["configured"] = bool(settings.gemini_api_key)
            provider_info["details"] = {
                "note": "Data sent to Google Gemini API"
            }
        elif settings.llm_provider == "deepseek":
            provider_info["configured"] = bool(settings.deepseek_api_key)
            provider_info["details"] = {
                "note": "Data sent to DeepSeek API"
            }

        return APIResponse(
            success=True,
            message=f"Active LLM provider: {settings.llm_provider}",
            data=provider_info
        )

    except Exception as e:
        logger.error(f"Failed to check LLM provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))
