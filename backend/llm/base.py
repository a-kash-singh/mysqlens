"""
Base LLM Provider interface for MySQLens.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def generate_recommendation(
        self,
        query: str,
        schema_context: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendation for a query.
        
        Args:
            query: The SQL query to analyze
            schema_context: Schema information for relevant tables
            metrics: Performance metrics for the query
            
        Returns:
            Dictionary with recommendation details
        """
        pass
    
    @abstractmethod
    async def analyze_query(
        self,
        query: str,
        execution_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query and provide insights.
        
        Args:
            query: The SQL query to analyze
            execution_plan: Optional execution plan data
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    def _build_prompt(self, query: str, schema_context: str, metrics: Dict[str, Any]) -> str:
        """Build the prompt for the LLM."""
        return f"""You are a MySQL database performance optimization expert. Analyze the following query and provide optimization recommendations.

Query:
{query}

Schema Context:
{schema_context}

Performance Metrics:
- Total execution time: {metrics.get('total_time', 0)} microseconds
- Number of calls: {metrics.get('calls', 0)}
- Average execution time: {metrics.get('mean_time', 0)} microseconds
- Rows examined: {metrics.get('rows_examined', 0)}
- Rows sent: {metrics.get('rows_sent', 0)}
- Temporary tables: {metrics.get('tmp_tables', 0)}
- Temporary disk tables: {metrics.get('tmp_disk_tables', 0)}

Please provide:
1. A clear analysis of the performance issues
2. Specific index recommendations (if applicable)
3. Query rewrite suggestions (if applicable)
4. Configuration recommendations (if applicable)
5. Estimated performance improvement percentage
6. Risk level (low, medium, high)

Format your response as JSON with the following structure:
{{
    "analysis": "Brief analysis of the query performance",
    "recommendations": [
        {{
            "type": "index|rewrite|config",
            "title": "Short title",
            "description": "Detailed description",
            "sql_fix": "SQL to apply the fix (if applicable)",
            "estimated_improvement": 50,
            "confidence_score": 85,
            "risk_level": "low|medium|high"
        }}
    ]
}}"""

