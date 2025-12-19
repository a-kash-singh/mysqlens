"""
LLM Provider Factory for MySQLens.
"""

import logging
from typing import Optional
from llm.base import BaseLLMProvider
from llm.gemini_provider import GeminiProvider
from llm.openai_provider import OpenAIProvider
from config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> Optional[BaseLLMProvider]:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider (gemini, openai, deepseek)
            
        Returns:
            LLM provider instance or None if not configured
        """
        provider_name = provider_name or settings.llm_provider
        
        try:
            if provider_name == "gemini" and settings.gemini_api_key:
                logger.info("Creating Gemini provider")
                return GeminiProvider(
                    api_key=settings.gemini_api_key,
                    model="gemini-2.0-flash-exp"
                )
            
            elif provider_name == "openai" and settings.openai_api_key:
                logger.info("Creating OpenAI provider")
                return OpenAIProvider(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model
                )
            
            elif provider_name == "deepseek" and settings.deepseek_api_key:
                logger.info("Creating DeepSeek provider (using OpenAI-compatible API)")
                # DeepSeek uses OpenAI-compatible API
                from openai import AsyncOpenAI
                provider = OpenAIProvider(
                    api_key=settings.deepseek_api_key,
                    model="deepseek-chat"
                )
                provider.client = AsyncOpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                return provider
            
            else:
                logger.warning(f"No API key configured for provider: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating LLM provider: {e}")
            return None
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available/configured providers."""
        available = []
        
        if settings.gemini_api_key:
            available.append("gemini")
        if settings.openai_api_key:
            available.append("openai")
        if settings.deepseek_api_key:
            available.append("deepseek")
        
        return available


llm_factory = LLMFactory()

