"""
OpenAI LLM Provider for MySQLens.
"""

import logging
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_recommendation(
        self,
        query: str,
        schema_context: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimization recommendation using OpenAI."""
        try:
            prompt = self._build_prompt(query, schema_context, metrics)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a MySQL database performance optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            text = response.choices[0].message.content
            
            try:
                parsed = json.loads(text)
                return parsed
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from OpenAI response")
                return self._fallback_recommendation(query, metrics)
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return self._fallback_recommendation(query, metrics)
    
    async def analyze_query(
        self,
        query: str,
        execution_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a query using OpenAI."""
        try:
            plan_text = json.dumps(execution_plan, indent=2) if execution_plan else "No execution plan available"
            
            prompt = f"""Analyze this MySQL query and provide insights:

Query:
{query}

Execution Plan:
{plan_text}

Provide a brief analysis of potential performance issues and optimization opportunities."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a MySQL database performance expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1024
            )
            
            text = response.choices[0].message.content
            return {"analysis": text}
                
        except Exception as e:
            logger.error(f"Error analyzing query with OpenAI: {e}")
            return {"analysis": f"Error: {str(e)}"}
    
    def _fallback_recommendation(self, query: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback recommendation using heuristics."""
        recommendations = []
        
        if metrics.get('rows_examined', 0) > metrics.get('rows_sent', 0) * 10:
            recommendations.append({
                "type": "index",
                "title": "High Row Examination Ratio",
                "description": "This query examines significantly more rows than it returns. Consider adding indexes on WHERE clause columns.",
                "sql_fix": None,
                "estimated_improvement": 30,
                "confidence_score": 70,
                "risk_level": "low"
            })
        
        if metrics.get('tmp_disk_tables', 0) > 0:
            recommendations.append({
                "type": "config",
                "title": "Temporary Tables on Disk",
                "description": "Query is creating temporary tables on disk. Increase tmp_table_size and max_heap_table_size.",
                "sql_fix": None,
                "estimated_improvement": 20,
                "confidence_score": 80,
                "risk_level": "low"
            })
        
        return {
            "analysis": "Heuristic-based analysis.",
            "recommendations": recommendations
        }

