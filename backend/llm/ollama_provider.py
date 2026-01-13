"""
Ollama Provider for local LLM inference in MySQLens.
"""

import logging
import json
import re
from typing import Dict, Any, Optional
import aiohttp

from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local LLM inference."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama base URL (e.g., http://localhost:11434)
            model: Model name (e.g., llama3, sqlcoder:7b)
        """
        super().__init__(api_key=None, model=model or "llama3")
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"
        logger.info(f"Initialized Ollama provider with model: {self.model}")

    @property
    def name(self) -> str:
        """Get provider name."""
        return "ollama"

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.model

    async def generate_recommendation(
        self,
        query: str,
        schema_context: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendation for a query using Ollama.

        Args:
            query: The SQL query to analyze
            schema_context: Schema information for relevant tables
            metrics: Performance metrics for the query

        Returns:
            Dictionary with recommendation details
        """
        try:
            prompt = self._build_prompt(query, schema_context, metrics)

            # Use analyze method for JSON-formatted response
            result = await self.analyze(prompt, max_tokens=2000)

            if isinstance(result, dict) and "error" in result:
                logger.error(f"Ollama error: {result['error']}")
                return {
                    "error": result["error"],
                    "recommendations": []
                }

            return result

        except Exception as e:
            logger.error(f"Error in Ollama generate_recommendation: {e}")
            return {
                "error": str(e),
                "recommendations": []
            }

    async def analyze_query(
        self,
        query: str,
        execution_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query and provide insights using Ollama.

        Args:
            query: The SQL query to analyze
            execution_plan: Optional execution plan data

        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = f"""You are a MySQL database performance expert. Analyze this query:

{query}

{'Execution Plan: ' + json.dumps(execution_plan, indent=2) if execution_plan else ''}

Provide a brief analysis including:
1. Query complexity assessment
2. Potential performance concerns
3. Optimization opportunities

Format as JSON:
{{
    "complexity": "low|medium|high",
    "concerns": ["concern1", "concern2"],
    "opportunities": ["opportunity1", "opportunity2"],
    "summary": "Brief summary"
}}"""

            result = await self.analyze(prompt, max_tokens=1000)
            return result

        except Exception as e:
            logger.error(f"Error in Ollama analyze_query: {e}")
            return {
                "error": str(e),
                "complexity": "unknown",
                "concerns": [],
                "opportunities": []
            }

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": max_tokens
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error ({response.status}): {error_text}")
                        return f"Error: Ollama returned status {response.status}"

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            return "Error: Cannot connect to Ollama. Is it running?"
        except Exception as e:
            logger.error(f"Error calling Ollama generate: {e}")
            return f"Error: {str(e)}"

    async def analyze(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Analyze and return JSON response using Ollama.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with analysis results
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",  # Request JSON output
                "options": {
                    "temperature": 0.1,  # Lower temperature for more deterministic output
                    "num_predict": max_tokens
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "{}")

                        # Try to parse JSON from response
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError:
                            # Try to extract JSON from text
                            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                            if json_match:
                                try:
                                    return json.loads(json_match.group(0))
                                except json.JSONDecodeError:
                                    pass

                            logger.warning(f"Could not parse JSON from Ollama response: {response_text[:200]}")
                            return {
                                "error": "Could not parse JSON response",
                                "raw_response": response_text
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error ({response.status}): {error_text}")
                        return {
                            "error": f"Ollama returned status {response.status}",
                            "details": error_text
                        }

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            return {
                "error": "Cannot connect to Ollama. Is it running?",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error calling Ollama analyze: {e}")
            return {
                "error": str(e)
            }
