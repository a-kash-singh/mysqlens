#!/usr/bin/env python3
"""
Advanced LLM Benchmarking Suite for MySQLens.
Runs Golden Dataset scenarios, captures full context (prompts, raw responses),
and validates LLM recommendations against expected outcomes.
"""

import requests
import time
import sys
import os
import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
ANALYZE_URL = f"{API_BASE_URL}/api/ai/analyze"
HEALTH_URL = f"{API_BASE_URL}/health"

# Golden Dataset Scenarios for MySQL
SCENARIOS = [
    {
        "id": "A",
        "name": "The Slam Dunk (Must Suggest Index)",
        "query": "SELECT * FROM demo_orders WHERE user_id = 5678",
        "expected_category": "INDEX",
        "description": "Large table, no index on user_id. Should suggest adding an index.",
        "expected_keywords": ["CREATE INDEX", "user_id"]
    },
    {
        "id": "B",
        "name": "The Trap (Must Not Suggest Index)",
        "query": "INSERT INTO demo_orders (user_id, total_amount) VALUES (123, 45.67)",
        "expected_category": "ADVISORY",
        "description": "Insert statement. Should NOT suggest indexes on INSERT.",
        "fail_if_contains": ["CREATE INDEX"]
    },
    {
        "id": "C",
        "name": "The N+1 Query (Rewrite Suggestion)",
        "query": "SELECT o.id, (SELECT username FROM demo_users WHERE id = o.user_id) FROM demo_orders o LIMIT 100",
        "expected_category": "REWRITE",
        "description": "Correlated subquery. Should suggest JOIN rewrite.",
        "expected_keywords": ["JOIN"]
    },
    {
        "id": "D",
        "name": "The Function on Column (Index Not Usable)",
        "query": "SELECT * FROM demo_users WHERE YEAR(created_at) = 2024",
        "expected_category": "REWRITE",
        "description": "Function on indexed column prevents index usage. Should suggest range rewrite.",
        "expected_keywords": [">=", "created_at", "BETWEEN"]
    },
    {
        "id": "E",
        "name": "The Missing JOIN Index",
        "query": "SELECT p.name, r.rating FROM demo_products p JOIN demo_reviews r ON p.id = r.product_id WHERE r.rating = 5",
        "expected_category": "INDEX",
        "description": "JOIN on product_id which is missing an index.",
        "expected_keywords": ["INDEX", "product_id"]
    },
    {
        "id": "F",
        "name": "The SELECT * Anti-pattern",
        "query": "SELECT * FROM demo_user_activity WHERE activity_type = 'search'",
        "expected_category": "REWRITE",
        "description": "SELECT * on large table. Should suggest selecting specific columns.",
        "expected_keywords": ["specific columns", "SELECT"]
    },
    {
        "id": "G",
        "name": "The JSON Query (Virtual Column)",
        "query": "SELECT username FROM demo_users WHERE JSON_EXTRACT(profile_data, '$.city') = 'Berlin'",
        "expected_category": "INDEX",
        "description": "JSON query without virtual column. Should suggest generated column with index.",
        "expected_keywords": ["GENERATED", "INDEX", "JSON"]
    },
]

# Results storage
benchmark_results = []


def check_api_health():
    """Check if the API is running and healthy."""
    try:
        resp = requests.get(HEALTH_URL, timeout=5)
        if resp.status_code == 200:
            logger.info("✅ API health check passed")
            return True
        else:
            logger.error(f"❌ API health check failed: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to API: {e}")
        return False


def run_scenario(scenario):
    """Run a single benchmark scenario."""
    logger.info(f"\n{'='*60}")
    logger.info(f"[Scenario {scenario['id']}] {scenario['name']}")
    logger.info(f"Query: {scenario['query'][:80]}...")
    logger.info(f"Expected: {scenario['expected_category']}")
    
    result = {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "query": scenario["query"],
        "expected_category": scenario["expected_category"],
        "timestamp": datetime.now().isoformat(),
        "passed": False,
        "actual_category": None,
        "response": None,
        "error": None,
        "duration_ms": 0
    }
    
    try:
        payload = {"query": scenario["query"]}
        
        start_time = time.time()
        response = requests.post(ANALYZE_URL, json=payload, timeout=120)
        duration = (time.time() - start_time) * 1000
        result["duration_ms"] = round(duration, 2)
        
        if response.status_code != 200:
            result["error"] = f"API Error: {response.status_code} - {response.text}"
            logger.error(f"  ❌ {result['error']}")
            return result
        
        data = response.json()
        result["response"] = data
        
        # Extract category from response
        suggestion = data.get("suggestion", data.get("recommendations", [{}]))
        if isinstance(suggestion, list) and len(suggestion) > 0:
            suggestion = suggestion[0]
        
        actual_category = suggestion.get("category", suggestion.get("type", "UNKNOWN")).upper()
        result["actual_category"] = actual_category
        
        # Get SQL suggestion
        sql_suggestion = suggestion.get("sql", suggestion.get("sql_fix", ""))
        reasoning = suggestion.get("reasoning", suggestion.get("description", ""))
        
        logger.info(f"  Actual Category: {actual_category}")
        logger.info(f"  Duration: {duration:.0f}ms")
        
        # Validate category
        category_match = actual_category == scenario["expected_category"]
        
        # Validate keywords
        keywords_found = True
        if "expected_keywords" in scenario:
            combined_text = f"{sql_suggestion} {reasoning}".upper()
            for keyword in scenario["expected_keywords"]:
                if keyword.upper() not in combined_text:
                    keywords_found = False
                    logger.warning(f"  ⚠️ Missing expected keyword: {keyword}")
        
        # Check fail conditions
        fail_condition_triggered = False
        if "fail_if_contains" in scenario:
            combined_text = f"{sql_suggestion} {reasoning}".upper()
            for fail_keyword in scenario["fail_if_contains"]:
                if fail_keyword.upper() in combined_text:
                    fail_condition_triggered = True
                    logger.error(f"  ❌ Contains forbidden keyword: {fail_keyword}")
        
        # Determine pass/fail
        result["passed"] = category_match and keywords_found and not fail_condition_triggered
        
        if result["passed"]:
            logger.info(f"  ✅ PASSED")
        else:
            if not category_match:
                logger.error(f"  ❌ FAILED: Expected {scenario['expected_category']}, got {actual_category}")
            elif fail_condition_triggered:
                logger.error(f"  ❌ FAILED: Contains forbidden content")
            else:
                logger.error(f"  ❌ FAILED: Missing expected keywords")
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout (120s)"
        logger.error(f"  ❌ {result['error']}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"  ❌ Error: {e}")
    
    return result


def save_results(results, output_file=None):
    """Save benchmark results to JSON file."""
    if output_file is None:
        output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    
    summary = {
        "run_timestamp": datetime.now().isoformat(),
        "api_url": API_BASE_URL,
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "pass_rate": round(sum(1 for r in results if r["passed"]) / len(results) * 100, 1) if results else 0,
        "scenarios": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_path}")
    return summary


def print_summary(summary):
    """Print benchmark summary."""
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Scenarios: {summary['total_scenarios']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Pass Rate: {summary['pass_rate']}%")
    logger.info("=" * 60)
    
    if summary['pass_rate'] == 100:
        logger.info("\n🎉 GOLDEN DATASET SUCCESS - ALL SCENARIOS PASSED!")
    else:
        logger.info("\n⚠️  SOME SCENARIOS FAILED - Review results for details")
        logger.info("\nFailed scenarios:")
        for scenario in summary['scenarios']:
            if not scenario['passed']:
                logger.info(f"  - [{scenario['scenario_id']}] {scenario['scenario_name']}")
                if scenario.get('error'):
                    logger.info(f"    Error: {scenario['error']}")


def main():
    """Main benchmark runner."""
    logger.info("=" * 60)
    logger.info("MySQLens LLM Benchmark Suite")
    logger.info("=" * 60)
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info(f"Scenarios: {len(SCENARIOS)}")
    
    # Check API health
    if not check_api_health():
        logger.error("\nAPI is not available. Please start the backend first:")
        logger.error("  docker-compose up -d mysqlens-api")
        logger.error("  or: cd backend && uvicorn main:app --reload")
        sys.exit(1)
    
    # Run all scenarios
    results = []
    for scenario in SCENARIOS:
        result = run_scenario(scenario)
        results.append(result)
        time.sleep(1)  # Small delay between scenarios
    
    # Save and display results
    summary = save_results(results)
    print_summary(summary)
    
    # Exit with appropriate code
    if summary['pass_rate'] == 100:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
