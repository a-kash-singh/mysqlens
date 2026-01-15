"""
LLM Response Validator and Guardrails for MySQLens.

Prevents hallucinations from local LLMs by validating:
- Response structure and required fields
- SQL syntax for suggested queries
- Index suggestions against actual schema
- Confidence scoring based on validation

Multi-layer validation ensures LLM recommendations are trustworthy.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, DML

logger = logging.getLogger(__name__)


class LLMValidator:
    """Validates and sanitizes LLM responses to prevent hallucinations."""

    def __init__(self):
        self.required_fields = ["score", "bottlenecks", "recommendations"]
        self.optional_fields = ["indexes", "rewrite"]

    def validate_response(
        self,
        llm_response: Dict[str, Any],
        query_text: str,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and sanitize LLM response.

        Args:
            llm_response: Raw response from LLM
            query_text: Original query being analyzed
            schema_context: Database schema information

        Returns:
            Validated response with confidence scores and warnings
        """
        validated = {
            "validated": True,
            "confidence": 1.0,
            "warnings": [],
            "analysis": {},
            "guardrails_applied": []
        }

        try:
            # Extract analysis from response
            analysis = llm_response.get("analysis", {})

            # 1. Validate structure
            structure_valid, structure_warnings = self._validate_structure(analysis)
            if not structure_valid:
                validated["confidence"] *= 0.5
                validated["warnings"].extend(structure_warnings)
                validated["guardrails_applied"].append("structure_validation")

            # 2. Validate score
            score_valid, sanitized_score = self._validate_score(analysis.get("score"))
            analysis["score"] = sanitized_score
            if not score_valid:
                validated["confidence"] *= 0.8
                validated["warnings"].append("Score was invalid or missing, defaulted to 50")
                validated["guardrails_applied"].append("score_sanitization")

            # 3. Validate bottlenecks
            bottlenecks_valid, sanitized_bottlenecks = self._validate_list_field(
                analysis.get("bottlenecks", []), "bottlenecks"
            )
            analysis["bottlenecks"] = sanitized_bottlenecks
            if not bottlenecks_valid:
                validated["confidence"] *= 0.9
                validated["guardrails_applied"].append("bottlenecks_sanitization")

            # 4. Validate recommendations
            recs_valid, sanitized_recs = self._validate_list_field(
                analysis.get("recommendations", []), "recommendations"
            )
            analysis["recommendations"] = sanitized_recs
            if not recs_valid:
                validated["confidence"] *= 0.9
                validated["guardrails_applied"].append("recommendations_sanitization")

            # 5. Validate indexes (if provided)
            if "indexes" in analysis:
                indexes_valid, sanitized_indexes, index_warnings = self._validate_indexes(
                    analysis.get("indexes", []),
                    schema_context,
                    query_text
                )
                analysis["indexes"] = sanitized_indexes
                validated["warnings"].extend(index_warnings)
                if not indexes_valid:
                    validated["confidence"] *= 0.7
                    validated["guardrails_applied"].append("index_validation")

            # 6. Validate query rewrite (if provided)
            if "rewrite" in analysis and analysis["rewrite"]:
                rewrite_valid, sanitized_rewrite, rewrite_warnings = self._validate_sql_rewrite(
                    analysis.get("rewrite"),
                    query_text
                )
                analysis["rewrite"] = sanitized_rewrite
                validated["warnings"].extend(rewrite_warnings)
                if not rewrite_valid:
                    validated["confidence"] *= 0.6
                    validated["guardrails_applied"].append("sql_validation")

            validated["analysis"] = analysis

            # Log validation results
            if validated["confidence"] < 1.0:
                logger.warning(
                    f"LLM response validation confidence: {validated['confidence']:.2f}, "
                    f"warnings: {len(validated['warnings'])}"
                )

            return validated

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "validated": False,
                "confidence": 0.0,
                "warnings": [f"Validation error: {str(e)}"],
                "analysis": {},
                "guardrails_applied": ["error_fallback"]
            }

    def _validate_structure(self, analysis: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate response has required structure."""
        warnings = []
        valid = True

        for field in self.required_fields:
            if field not in analysis:
                warnings.append(f"Missing required field: {field}")
                valid = False

        return valid, warnings

    def _validate_score(self, score: Any) -> Tuple[bool, int]:
        """Validate and sanitize performance score."""
        try:
            if score is None:
                return False, 50

            # Convert to int
            score_int = int(score)

            # Clamp to 0-100
            if score_int < 0 or score_int > 100:
                logger.warning(f"Score {score_int} out of range, clamping to 0-100")
                score_int = max(0, min(100, score_int))
                return False, score_int

            return True, score_int

        except (ValueError, TypeError):
            logger.warning(f"Invalid score: {score}, defaulting to 50")
            return False, 50

    def _validate_list_field(
        self,
        field_value: Any,
        field_name: str
    ) -> Tuple[bool, List[str]]:
        """Validate and sanitize list fields like bottlenecks and recommendations."""
        if not isinstance(field_value, list):
            logger.warning(f"{field_name} is not a list, converting")
            if isinstance(field_value, str):
                return False, [field_value]
            return False, []

        # Filter out empty or invalid entries
        sanitized = [
            str(item).strip()
            for item in field_value
            if item and str(item).strip()
        ]

        # Limit to reasonable number
        max_items = 10
        if len(sanitized) > max_items:
            logger.warning(f"{field_name} has {len(sanitized)} items, truncating to {max_items}")
            sanitized = sanitized[:max_items]
            return False, sanitized

        return True, sanitized

    def _validate_indexes(
        self,
        indexes: Any,
        schema_context: Optional[str],
        query_text: str
    ) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """Validate suggested indexes against schema."""
        warnings = []
        valid = True

        if not isinstance(indexes, list):
            warnings.append("Indexes field is not a list, ignoring")
            return False, [], warnings

        # Extract tables and columns from schema
        schema_tables, schema_columns = self._extract_schema_info(schema_context)

        # Extract tables from query
        query_tables = self._extract_tables_from_query(query_text)

        sanitized_indexes = []
        for idx in indexes:
            if not isinstance(idx, dict):
                warnings.append(f"Invalid index format: {idx}")
                valid = False
                continue

            # Validate index has required fields
            if "table" not in idx or "columns" not in idx:
                warnings.append(f"Index missing table or columns: {idx}")
                valid = False
                continue

            table = idx.get("table", "").strip()
            columns = idx.get("columns", [])

            if not isinstance(columns, list):
                if isinstance(columns, str):
                    columns = [c.strip() for c in columns.split(",")]
                else:
                    warnings.append(f"Invalid columns format for table {table}")
                    valid = False
                    continue

            # Validate table exists in schema or query
            if schema_tables and table not in schema_tables and table not in query_tables:
                warnings.append(
                    f"⚠️ Index suggests table '{table}' which may not exist. "
                    f"Possible hallucination - verify manually."
                )
                valid = False
                # Still include but mark as unverified
                idx["verified"] = False
                idx["warning"] = "Table not found in schema"
            else:
                idx["verified"] = True

            # Validate columns exist
            if schema_columns:
                invalid_columns = []
                for col in columns:
                    col_str = str(col).strip()
                    # Check if column exists for this table
                    if table in schema_columns:
                        if col_str not in schema_columns[table]:
                            invalid_columns.append(col_str)

                if invalid_columns:
                    warnings.append(
                        f"⚠️ Index on {table} suggests non-existent columns: {invalid_columns}. "
                        f"Possible hallucination - verify manually."
                    )
                    valid = False
                    idx["verified"] = False
                    idx["warning"] = f"Columns not found: {invalid_columns}"

            sanitized_indexes.append(idx)

        return valid, sanitized_indexes, warnings

    def _validate_sql_rewrite(
        self,
        rewrite: Any,
        original_query: str
    ) -> Tuple[bool, str, List[str]]:
        """Validate suggested SQL rewrite."""
        warnings = []
        valid = True

        if not rewrite or not isinstance(rewrite, str):
            return False, "", ["Query rewrite is empty or invalid"]

        rewrite = rewrite.strip()

        # 1. Basic SQL syntax validation
        try:
            parsed = sqlparse.parse(rewrite)
            if not parsed:
                warnings.append("⚠️ Suggested query could not be parsed. Verify syntax manually.")
                valid = False
        except Exception as e:
            warnings.append(f"⚠️ SQL syntax error in suggested query: {e}")
            valid = False

        # 2. Check it's a SELECT query (don't allow DML/DDL hallucinations)
        if not rewrite.strip().upper().startswith("SELECT"):
            warnings.append("⚠️ Suggested query is not a SELECT statement. Rejecting for safety.")
            return False, "", warnings

        # 3. Ensure no dangerous keywords (DROP, DELETE, UPDATE, etc.)
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"]
        upper_rewrite = rewrite.upper()
        for keyword in dangerous_keywords:
            if keyword in upper_rewrite:
                warnings.append(f"⚠️ Suggested query contains dangerous keyword '{keyword}'. Rejecting.")
                return False, "", warnings

        # 4. Compare with original query structure
        if not self._queries_seem_equivalent(original_query, rewrite):
            warnings.append(
                "⚠️ Suggested query structure differs significantly from original. "
                "Verify it produces same results."
            )
            valid = False

        return valid, rewrite, warnings

    def _extract_schema_info(
        self,
        schema_context: Optional[str]
    ) -> Tuple[Set[str], Dict[str, Set[str]]]:
        """Extract tables and columns from schema context."""
        tables = set()
        columns = {}  # table -> set of columns

        if not schema_context:
            return tables, columns

        try:
            # Parse schema context for table and column names
            # Format: "Table: users, Columns: id, name, email"
            lines = schema_context.split("\n")
            current_table = None

            for line in lines:
                line = line.strip()

                # Look for table definitions
                if "Table:" in line or "table:" in line.lower():
                    match = re.search(r'[Tt]able[:\s]+([a-zA-Z0-9_]+)', line)
                    if match:
                        current_table = match.group(1)
                        tables.add(current_table)
                        columns[current_table] = set()

                # Look for column definitions
                if current_table and ("Columns:" in line or "columns:" in line.lower()):
                    match = re.search(r'[Cc]olumns[:\s]+(.+)', line)
                    if match:
                        col_str = match.group(1)
                        cols = [c.strip() for c in col_str.split(",")]
                        columns[current_table].update(cols)

        except Exception as e:
            logger.warning(f"Failed to parse schema context: {e}")

        return tables, columns

    def _extract_tables_from_query(self, query: str) -> Set[str]:
        """Extract table names from SQL query."""
        tables = set()

        try:
            parsed = sqlparse.parse(query)
            for statement in parsed:
                for token in statement.tokens:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.add(identifier.get_real_name())
                    elif isinstance(token, Identifier):
                        tables.add(token.get_real_name())
        except Exception as e:
            logger.warning(f"Failed to extract tables from query: {e}")

        return tables

    def _queries_seem_equivalent(self, original: str, rewrite: str) -> bool:
        """
        Heuristic check if queries seem equivalent.

        Checks:
        - Same tables referenced
        - Same general structure
        - Not completely different
        """
        try:
            orig_tables = self._extract_tables_from_query(original)
            rewrite_tables = self._extract_tables_from_query(rewrite)

            # If tables differ significantly, queries may not be equivalent
            if orig_tables and rewrite_tables:
                overlap = len(orig_tables.intersection(rewrite_tables))
                total = len(orig_tables.union(rewrite_tables))

                # At least 50% table overlap
                if total > 0 and overlap / total < 0.5:
                    return False

            return True

        except Exception:
            # If we can't determine, assume equivalent (conservative)
            return True


# Global validator instance
llm_validator = LLMValidator()
