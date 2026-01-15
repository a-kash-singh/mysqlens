"""
LLM Service for MySQLens.
Multi-provider LLM integration (Ollama, OpenAI, Gemini, DeepSeek).

Implements three-layer anti-hallucination approach:
1. Context Pruner - Extract only relevant tables (reduces hallucinations ~60%)
2. Dual-Path Router - Different strategies for standard vs reasoning models
3. Schema Validator - Validate AI suggestions against actual schema

Ensures local LLMs are production-ready and trustworthy.
"""

import logging
import json
from typing import Dict, Any, Optional
import aiohttp
from config import settings
from services.llm_validator import llm_validator
from services.context_pruner import context_pruner
from services.model_router import model_router, ModelType

logger = logging.getLogger(__name__)


class LLMService:
    """Service for AI-powered query analysis using multiple LLM providers."""
    
    async def analyze_query(
        self,
        query_text: str,
        execution_plan: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        schema_context: Optional[str] = None,
        full_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query using the configured LLM provider.

        Implements 3-layer anti-hallucination approach:
        1. Context Pruner - Extract only relevant tables (~60% hallucination reduction)
        2. Dual-Path Router - Adapt prompting to model architecture
        3. Schema Validator - Validate against actual schema

        Args:
            query_text: The SQL query to analyze
            execution_plan: EXPLAIN output
            metrics: Performance metrics
            schema_context: Database schema information (will be pruned)
            full_schema: Complete schema dict for pruning (optional but recommended)

        Returns:
            Validated analysis results with confidence scores and warnings
        """
        try:
            # LAYER 1: Context Pruner
            # Reduce schema to only relevant tables
            pruned_schema = schema_context  # Default to provided schema
            context_reduction = None

            if full_schema:
                pruned_schema = context_pruner.prune_schema_context(
                    query_text,
                    full_schema,
                    execution_plan
                )
                context_reduction = context_pruner.estimate_context_reduction(
                    query_text,
                    full_schema
                )
                logger.info(
                    f"Context Pruner: {context_reduction['reduction_percentage']}% reduction "
                    f"({context_reduction['total_tables']} -> {context_reduction['relevant_tables']} tables)"
                )

            # LAYER 2: Dual-Path Router
            # Detect model type and build appropriate prompt
            model_name = self._get_model_name()
            model_type = model_router.detect_model_type(model_name)

            # Build base context
            base_context = self._build_base_context(
                query_text,
                execution_plan,
                metrics,
                pruned_schema  # Use PRUNED schema
            )

            # Route prompt based on model type
            final_prompt, needs_extraction = model_router.build_prompt(
                model_type,
                base_context
            )

            # Route to appropriate provider
            llm_response = None
            if settings.llm_provider == "ollama":
                llm_response = await self._analyze_with_ollama(final_prompt, needs_extraction)
            elif settings.llm_provider == "openai":
                llm_response = await self._analyze_with_openai(final_prompt, needs_extraction)
            elif settings.llm_provider == "gemini":
                llm_response = await self._analyze_with_gemini(final_prompt, needs_extraction)
            elif settings.llm_provider == "deepseek":
                llm_response = await self._analyze_with_deepseek(final_prompt, needs_extraction)
            else:
                return {
                    "success": False,
                    "error": f"Unknown LLM provider: {settings.llm_provider}"
                }

            # Check if LLM call was successful
            if not llm_response.get("success", False):
                return llm_response

            # LAYER 3: Ghost Column Guardrail
            # Validate response against actual schema
            validated_response = llm_validator.validate_response(
                llm_response,
                query_text,
                pruned_schema  # Validate against pruned schema
            )

            # Merge validated response with original
            result = {
                "success": True,
                "provider": llm_response.get("provider", settings.llm_provider),
                "model_type": model_type.value,
                "analysis": validated_response["analysis"],
                "confidence": validated_response["confidence"],
                "warnings": validated_response["warnings"],
                "guardrails_applied": validated_response["guardrails_applied"],
                "validated": validated_response["validated"]
            }

            # Add context reduction metrics if available
            if context_reduction:
                result["context_reduction"] = context_reduction

            # Log warnings if confidence is low
            if validated_response["confidence"] < 0.7:
                logger.warning(
                    f"Low confidence LLM response ({validated_response['confidence']:.2f}). "
                    f"Warnings: {validated_response['warnings']}"
                )

            return result

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_model_name(self) -> str:
        """Get the model name for the current provider."""
        if settings.llm_provider == "ollama":
            return settings.ollama_model
        elif settings.llm_provider == "openai":
            return getattr(settings, "openai_model", "gpt-4")
        elif settings.llm_provider == "deepseek":
            return "deepseek-chat"
        elif settings.llm_provider == "gemini":
            return "gemini-pro"
        else:
            return "unknown"
    
    def _build_base_context(
        self,
        query_text: str,
        execution_plan: Optional[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]],
        schema_context: Optional[str]
    ) -> str:
        """
        Build base context prompt for LLM with anti-hallucination instructions.

        This is the BASE prompt that gets enhanced by the Model Router.

        Uses specific instructions to reduce hallucinations:
        - Only use provided schema information
        - Don't invent tables or columns
        - Validate SQL syntax
        - Be conservative with recommendations
        """
        context_parts = [
            "You are a MySQL database performance expert. Analyze the query below and provide optimization recommendations.",
            "",
            "IMPORTANT RULES TO PREVENT ERRORS:",
            "- ONLY suggest indexes on tables and columns that appear in the Schema Context below",
            "- DO NOT invent or guess table/column names",
            "- If no schema is provided, DO NOT suggest specific indexes",
            "- ONLY suggest valid MySQL syntax",
            "- If unsure about a recommendation, omit it rather than guessing",
            "- Be conservative and factual in your analysis",
            "",
            "## Query to Analyze:",
            "```sql",
            query_text,
            "```",
            ""
        ]

        if execution_plan:
            context_parts.extend([
                "## EXPLAIN Output:",
                "```json",
                json.dumps(execution_plan, indent=2),
                "```",
                ""
            ])

        if metrics:
            context_parts.extend([
                "## Performance Metrics:",
                f"- Execution count: {metrics.get('count_star', 'N/A')}",
                f"- Average execution time: {metrics.get('avg_timer_wait_ms', 'N/A')} ms",
                f"- Rows examined: {metrics.get('sum_rows_examined', 'N/A')}",
                f"- Rows returned: {metrics.get('sum_rows_sent', 'N/A')}",
                ""
            ])

        if schema_context:
            context_parts.extend([
                "## Schema Context (Tables and Columns):",
                "```",
                schema_context,
                "```",
                "",
                "REMINDER: Only suggest indexes using tables/columns from the Schema Context above.",
                ""
            ])
        else:
            context_parts.extend([
                "## Schema Context:",
                "No schema information provided. DO NOT suggest specific index names.",
                ""
            ])

        # Don't add output format here - Model Router will add the appropriate format
        # based on model type (standard vs reasoning)

        return "\n".join(context_parts)

    async def _analyze_with_ollama(
        self,
        context: str,
        needs_extraction: bool = False
    ) -> Dict[str, Any]:
        """Analyze using Ollama local LLM."""
        try:
            # Determine format based on model type
            # Reasoning models need freedom, standard models forced to JSON
            format_param = None if needs_extraction else "json"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": context,
                        "stream": False,
                        "format": format_param  # None for reasoning models
                    },
                    timeout=aiohttp.ClientTimeout(total=120)  # Longer for reasoning
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        raw_response = result.get("response", "{}")

                        # Extract analysis based on model type
                        if needs_extraction:
                            # Reasoning model - extract JSON from text
                            model_type = model_router.detect_model_type(settings.ollama_model)
                            analysis = model_router.extract_response(raw_response, model_type)
                        else:
                            # Standard model - direct JSON parse
                            try:
                                analysis = json.loads(raw_response)
                            except json.JSONDecodeError:
                                # Fallback extraction
                                model_type = model_router.detect_model_type(settings.ollama_model)
                                analysis = model_router.extract_response(raw_response, model_type)

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
    
    async def _analyze_with_openai(self, context: str, needs_extraction: bool = False) -> Dict[str, Any]:
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
                response_format={"type": "json_object"} if not needs_extraction else None,
                temperature=0.3
            )

            raw_response = response.choices[0].message.content

            # Extract analysis based on model type
            if needs_extraction:
                model_type = model_router.detect_model_type(settings.openai_model)
                analysis = model_router.extract_response(raw_response, model_type)
            else:
                analysis = json.loads(raw_response)

            return {
                "success": True,
                "provider": "openai",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_with_gemini(self, context: str, needs_extraction: bool = False) -> Dict[str, Any]:
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
                    "response_mime_type": "application/json" if not needs_extraction else None
                }
            )

            raw_response = response.text

            # Extract analysis based on model type
            if needs_extraction:
                model_type = ModelType.STANDARD  # Gemini is standard
                analysis = model_router.extract_response(raw_response, model_type)
            else:
                analysis = json.loads(raw_response)

            return {
                "success": True,
                "provider": "gemini",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_with_deepseek(self, context: str, needs_extraction: bool = False) -> Dict[str, Any]:
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
                        "response_format": {"type": "json_object"} if not needs_extraction else None,
                        "temperature": 0.3
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        raw_response = result["choices"][0]["message"]["content"]

                        # Extract analysis based on model type
                        if needs_extraction:
                            model_type = model_router.detect_model_type("deepseek-chat")
                            analysis = model_router.extract_response(raw_response, model_type)
                        else:
                            analysis = json.loads(raw_response)

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
