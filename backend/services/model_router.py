"""
Dual-Path Router for MySQLens.

Routes LLM requests based on model architecture:
- Path A (Standard Models): Force JSON Chain-of-Thought
- Path B (Reasoning Models): Let model output raw reasoning, extract JSON

Optimizes prompting strategy for different model types.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model architecture types."""
    STANDARD = "standard"  # Llama, Qwen, SQLCoder - "lazy" models
    REASONING = "reasoning"  # DeepSeek R1 - needs space to "think"
    UNKNOWN = "unknown"


class ModelRouter:
    """
    Routes prompts based on model architecture.

    Insight:
    Standard Models (Qwen, Llama) rush to solutions - need forced Chain-of-Thought.
    Reasoning Models (DeepSeek R1) need space to think - allow natural reasoning.

    Solution: Detect model type and adjust prompting strategy.
    """

    def __init__(self):
        # Model classification based on name patterns
        self.reasoning_models = [
            "deepseek-r1",
            "deepseek-reasoner",
            "o1",  # OpenAI o1 series
            "qwq",  # Qwen reasoning model
        ]

        self.standard_models = [
            "llama",
            "qwen",
            "sqlcoder",
            "codestral",
            "mistral",
            "phi",
            "gemma",
        ]

    def detect_model_type(self, model_name: str) -> ModelType:
        """
        Detect model architecture from model name.

        Args:
            model_name: Name of the model (e.g., "llama3.2:latest", "deepseek-r1")

        Returns:
            ModelType enum
        """
        model_lower = model_name.lower()

        # Check for reasoning models first (more specific)
        for reasoning_pattern in self.reasoning_models:
            if reasoning_pattern in model_lower:
                logger.info(f"Detected REASONING model: {model_name}")
                return ModelType.REASONING

        # Check for standard models
        for standard_pattern in self.standard_models:
            if standard_pattern in model_lower:
                logger.info(f"Detected STANDARD model: {model_name}")
                return ModelType.STANDARD

        logger.warning(f"Unknown model type: {model_name}, defaulting to STANDARD")
        return ModelType.UNKNOWN

    def build_prompt(
        self,
        model_type: ModelType,
        base_context: str
    ) -> Tuple[str, bool]:
        """
        Build appropriate prompt based on model type.

        Returns:
            Tuple of (prompt, needs_json_extraction)
            - needs_json_extraction: True if response needs regex parsing
        """
        if model_type == ModelType.REASONING:
            return self._build_reasoning_prompt(base_context), True
        else:
            return self._build_standard_prompt(base_context), False

    def _build_standard_prompt(self, base_context: str) -> str:
        """
        Path A: Force JSON Chain-of-Thought for standard models.

        Strategy: Require "reasoning" field before "sql_fix" field.
        This forces the model to plan before it acts.
        """
        # Add forced CoT structure to existing context
        cot_instructions = """

## IMPORTANT - Chain of Thought Required:
You MUST structure your response as JSON with these fields IN THIS ORDER:

1. "reasoning" (string): Your step-by-step analysis of the query:
   - What is the query trying to do?
   - What are the performance bottlenecks?
   - Why do you recommend these optimizations?
   - Think through your logic step-by-step FIRST

2. "score" (integer 0-100): Performance score AFTER reasoning

3. "bottlenecks" (array): Identified issues BASED ON your reasoning

4. "recommendations" (array): Suggestions DERIVED FROM your analysis

5. "indexes" (optional array): Only if you reasoned that indexes are needed

6. "rewrite" (optional string): Only if you reasoned a rewrite would help

CRITICAL: Fill the "reasoning" field FIRST. This forces you to think before suggesting changes.

Example structure:
```json
{
  "reasoning": "The query performs a full table scan on the users table because there's no index on the email column. Looking at the EXPLAIN output, we see 'type: ALL' which confirms a full scan. This is inefficient when searching by email. An index on the email column would allow direct lookup instead of scanning all rows. The query structure is simple, so no rewrite is needed, just an index.",
  "score": 45,
  "bottlenecks": ["Full table scan on users table", "No index on email column"],
  "recommendations": ["Add index on email column for faster lookups"],
  "indexes": [{"table": "users", "columns": ["email"], "type": "BTREE"}]
}
```
"""
        return base_context + cot_instructions

    def _build_reasoning_prompt(self, base_context: str) -> str:
        """
        Path B: Let reasoning models output raw reasoning.

        Strategy: Allow natural reasoning flow, extract JSON at the end.
        DeepSeek R1 and similar models perform better when allowed to
        "talk to themselves" in natural language first.
        """
        reasoning_instructions = """

## Output Format for Reasoning Models:
You are a reasoning model. Take your time to think through the problem.

1. First, OUTPUT YOUR REASONING in natural language:
   - Analyze the query step-by-step
   - Think through what's happening
   - Consider different optimization strategies
   - Talk through your logic

2. Then, AFTER your reasoning, output your final analysis as JSON:
   - Wrap the JSON in <JSON> tags
   - Include all required fields

Example output:
```
Let me analyze this query step by step. First, I notice it's selecting from the users table with a WHERE clause on the email column. Looking at the EXPLAIN output, I see "type: ALL" which means it's doing a full table scan - that's our main bottleneck.

Why is this happening? Because there's no index on the email column. Every time this query runs, MySQL has to scan every single row in the users table to find matching emails. That's inefficient.

What should we do? The obvious solution is to add a BTREE index on the email column. This would allow MySQL to jump directly to matching rows instead of scanning everything. The query itself is fine - it's simple and clear. No rewrite needed.

Let me also check if there are any other issues... The SELECT * is pulling all columns, but without knowing the use case, I can't say if that's problematic. I'll mention it as a general recommendation.

<JSON>
{
  "score": 45,
  "bottlenecks": ["Full table scan on users table due to missing index on email"],
  "recommendations": ["Add BTREE index on email column", "Consider selecting only needed columns instead of SELECT *"],
  "indexes": [{"table": "users", "columns": ["email"], "type": "BTREE"}]
}
</JSON>
```

Take your time. Think it through. Output your reasoning, then the JSON.
"""
        return base_context + reasoning_instructions

    def extract_response(
        self,
        raw_response: str,
        model_type: ModelType
    ) -> Dict[str, Any]:
        """
        Extract structured response based on model type.

        Standard models: Direct JSON parsing
        Reasoning models: Extract JSON from <JSON> tags or end of response
        """
        if model_type == ModelType.REASONING:
            return self._extract_reasoning_response(raw_response)
        else:
            return self._extract_standard_response(raw_response)

    def _extract_standard_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Extract JSON from standard model response.

        These models should return JSON directly (because we forced it).
        """
        try:
            # Try direct JSON parse
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback: try to find JSON object in response
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error("Failed to extract JSON from standard model response")
            return {
                "error": "Could not parse response",
                "raw": raw_response[:500]
            }

    def _extract_reasoning_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Extract JSON from reasoning model response.

        These models output reasoning text first, then JSON.
        We use regex to extract the JSON payload.
        """
        # Method 1: Look for <JSON> tags
        json_tag_match = re.search(r'<JSON>(.*?)</JSON>', raw_response, re.DOTALL | re.IGNORECASE)
        if json_tag_match:
            try:
                json_str = json_tag_match.group(1).strip()
                parsed = json.loads(json_str)

                # Extract reasoning from before the JSON tag
                reasoning_text = raw_response[:json_tag_match.start()].strip()
                if reasoning_text and "reasoning" not in parsed:
                    parsed["reasoning"] = reasoning_text

                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"JSON in tags failed to parse: {e}")

        # Method 2: Look for last JSON object in response
        # Find all potential JSON objects
        json_objects = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw_response, re.DOTALL)
        json_matches = list(json_objects)

        if json_matches:
            # Take the last (most complete) JSON object
            last_match = json_matches[-1]
            try:
                json_str = last_match.group(0)
                parsed = json.loads(json_str)

                # Extract reasoning from before the JSON
                reasoning_text = raw_response[:last_match.start()].strip()
                if reasoning_text and "reasoning" not in parsed:
                    parsed["reasoning"] = reasoning_text

                return parsed
            except json.JSONDecodeError:
                pass

        # Method 3: Fallback - try to parse entire response
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            logger.error("Failed to extract JSON from reasoning model response")
            return {
                "error": "Could not extract JSON from reasoning output",
                "raw": raw_response[:500]
            }


# Global instance
model_router = ModelRouter()
