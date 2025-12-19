"""
Google Gemini LLM Provider for MySQLens.
"""

import logging
import json
import httpx
from typing import Dict, Any, Optional
from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    async def generate_recommendation(
        self,
        query: str,
        schema_context: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimization recommendation using Gemini."""
        try:
            prompt = self._build_prompt(query, schema_context, metrics)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.2,
                            "topP": 0.8,
                            "topK": 40,
                            "maxOutputTokens": 2048,
                        }
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Gemini API error: {response.text}")
                    return self._fallback_recommendation(query, metrics)
                
                result = response.json()
                
                # Extract the text from Gemini response
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Try to parse JSON from the response
                    try:
                        # Remove markdown code blocks if present
                        if '```json' in text:
                            text = text.split('```json')[1].split('```')[0].strip()
                        elif '```' in text:
                            text = text.split('```')[1].split('```')[0].strip()
                        
                        parsed = json.loads(text)
                        return parsed
                    except json.JSONDecodeError:
                        logger.warning("Could not parse JSON from Gemini response")
                        return self._fallback_recommendation(query, metrics)
                
                return self._fallback_recommendation(query, metrics)
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return self._fallback_recommendation(query, metrics)
    
    async def analyze_query(
        self,
        query: str,
        execution_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a query using Gemini."""
        try:
            plan_text = json.dumps(execution_plan, indent=2) if execution_plan else "No execution plan available"
            
            prompt = f"""Analyze this MySQL query and provide insights:

Query:
{query}

Execution Plan:
{plan_text}

Provide a brief analysis of potential performance issues and optimization opportunities."""
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.2,
                            "topP": 0.8,
                            "topK": 40,
                            "maxOutputTokens": 1024,
                        }
                    }
                )
                
                if response.status_code != 200:
                    return {"analysis": "Unable to analyze query at this time"}
                
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return {"analysis": text}
                
                return {"analysis": "No analysis available"}
                
        except Exception as e:
            logger.error(f"Error analyzing query with Gemini: {e}")
            return {"analysis": f"Error: {str(e)}"}
    
    def _fallback_recommendation(self, query: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback recommendation using heuristics."""
        recommendations = []
        
        # Check for missing indexes
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
        
        # Check for temporary tables on disk
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
            "analysis": "Heuristic-based analysis. Consider enabling AI analysis for more detailed insights.",
            "recommendations": recommendations
        }

