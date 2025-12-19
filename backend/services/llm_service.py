"""
LLM Service for MySQLens.
Multi-provider LLM integration (Ollama, OpenAI, Gemini, DeepSeek).
"""

import logging
import json
from typing import Dict, Any, Optional
import aiohttp
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for AI-powered query analysis using multiple LLM providers."""
    
    async def analyze_query(
        self,
        query_text: str,
        execution_plan: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query using the configured LLM provider.
        
        Args:
            query_text: The SQL query to analyze
            execution_plan: EXPLAIN output
            metrics: Performance metrics
            schema_context: Database schema information
            
        Returns:
            Analysis results with recommendations
        """
        try:
            # Build context for LLM
            context = self._build_context(query_text, execution_plan, metrics, schema_context)
            
            # Route to appropriate provider
            if settings.llm_provider == "ollama":
                return await self._analyze_with_ollama(context)
            elif settings.llm_provider == "openai":
                return await self._analyze_with_openai(context)
            elif settings.llm_provider == "gemini":
                return await self._analyze_with_gemini(context)
            elif settings.llm_provider == "deepseek":
                return await self._analyze_with_deepseek(context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown LLM provider: {settings.llm_provider}"
                }
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_context(
        self,
        query_text: str,
        execution_plan: Optional[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]],
        schema_context: Optional[str]
    ) -> str:
        """Build context prompt for LLM."""
        context_parts = [
            "You are a MySQL database performance expert. Analyze the following query and provide optimization recommendations.",
            "",
            "## Query:",
            query_text,
            ""
        ]
        
        if execution_plan:
            context_parts.extend([
                "## EXPLAIN Output:",
                json.dumps(execution_plan, indent=2),
                ""
            ])
        
        if metrics:
            context_parts.extend([
                "## Performance Metrics:",
                f"- Execution count: {metrics.get('count_star', 'N/A')}",
                f"- Average time: {metrics.get('avg_timer_wait_ms', 'N/A')} ms",
                f"- Rows examined: {metrics.get('sum_rows_examined', 'N/A')}",
                f"- Rows sent: {metrics.get('sum_rows_sent', 'N/A')}",
                ""
            ])
        
        if schema_context:
            context_parts.extend([
                "## Schema Context:",
                schema_context,
                ""
            ])
        
        context_parts.extend([
            "## Task:",
            "Provide:",
            "1. Performance assessment (score 0-100)",
            "2. Identified bottlenecks",
            "3. Specific optimization recommendations",
            "4. Suggested indexes (if applicable)",
            "5. Query rewrite suggestions (if applicable)",
            "",
            "Format your response as JSON with keys: score, bottlenecks, recommendations, indexes, rewrite"
        ])
        
        return "\n".join(context_parts)
    
    async def _analyze_with_ollama(self, context: str) -> Dict[str, Any]:
        """Analyze using Ollama local LLM."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": context,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis = json.loads(result.get("response", "{}"))
                        return {
                            "success": True,
                            "provider": "ollama",
                            "analysis": analysis
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Ollama API error: {error_text}"
                        }
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_with_openai(self, context: str) -> Dict[str, Any]:
        """Analyze using OpenAI API."""
        if not settings.openai_api_key:
            return {"success": False, "error": "OpenAI API key not configured"}
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a MySQL database performance expert."},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "provider": "openai",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_with_gemini(self, context: str) -> Dict[str, Any]:
        """Analyze using Google Gemini API."""
        if not settings.gemini_api_key:
            return {"success": False, "error": "Gemini API key not configured"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(
                context,
                generation_config={
                    "temperature": 0.3,
                    "response_mime_type": "application/json"
                }
            )
            
            analysis = json.loads(response.text)
            return {
                "success": True,
                "provider": "gemini",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_with_deepseek(self, context: str) -> Dict[str, Any]:
        """Analyze using DeepSeek API."""
        if not settings.deepseek_api_key:
            return {"success": False, "error": "DeepSeek API key not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a MySQL database performance expert."},
                            {"role": "user", "content": context}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis = json.loads(result["choices"][0]["message"]["content"])
                        return {
                            "success": True,
                            "provider": "deepseek",
                            "analysis": analysis
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"DeepSeek API error: {error_text}"}
        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
llm_service = LLMService()
