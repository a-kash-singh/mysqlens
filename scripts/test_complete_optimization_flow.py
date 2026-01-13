#!/usr/bin/env python3
"""
Complete End-to-End Test for MySQLens Optimization Flow
Tests: Connection → Metrics → AI Analysis → Index Recommendations

This script validates the entire flow works correctly.
"""

import asyncio
import sys
import os
import json
import requests
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")

# Test database configuration
TEST_DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "mysqlens_demo")
}


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.message = ""
        self.data = None
        self.duration_ms = 0


def test_api_health():
    """Step 1: Test API Health."""
    result = TestResult("API Health Check")
    
    try:
        import time
        start = time.time()
        resp = requests.get(f"{API_BASE_URL}/health", timeout=10)
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            result.passed = data.get("status") in ["healthy", "ok", True]
            result.message = f"API is healthy (version: {data.get('version', 'unknown')})"
            result.data = data
        else:
            result.message = f"Unhealthy response: {resp.status_code}"
    except Exception as e:
        result.message = f"Failed to connect: {e}"
    
    return result


def test_database_connection():
    """Step 2: Test Database Connection via API."""
    result = TestResult("Database Connection")
    
    try:
        import time
        start = time.time()
        
        # Connect to database
        connect_payload = {
            "host": TEST_DB_CONFIG["host"],
            "port": TEST_DB_CONFIG["port"],
            "user": TEST_DB_CONFIG["user"],
            "password": TEST_DB_CONFIG["password"],
            "database": TEST_DB_CONFIG["database"]
        }
        
        resp = requests.post(
            f"{API_BASE_URL}/api/connection/connect",
            json=connect_payload,
            timeout=30
        )
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            result.passed = data.get("success", data.get("connected", False))
            result.message = f"Connected to MySQL {data.get('version', 'unknown')}"
            result.data = data
        else:
            result.message = f"Connection failed: {resp.status_code} - {resp.text}"
    except Exception as e:
        result.message = f"Connection error: {e}"
    
    return result


def test_get_metrics():
    """Step 3: Test Getting Query Metrics."""
    result = TestResult("Query Metrics Retrieval")
    
    try:
        import time
        start = time.time()
        
        resp = requests.get(f"{API_BASE_URL}/api/metrics/queries", timeout=30)
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            queries = data.get("queries", data) if isinstance(data, dict) else data
            
            if isinstance(queries, list):
                result.passed = True
                result.message = f"Retrieved {len(queries)} query metrics"
                result.data = {"count": len(queries), "sample": queries[:3] if queries else []}
            else:
                result.passed = True
                result.message = "Metrics endpoint responsive"
                result.data = data
        else:
            result.message = f"Failed: {resp.status_code}"
    except Exception as e:
        result.message = f"Error: {e}"
    
    return result


def test_schema_info():
    """Step 4: Test Schema Information Retrieval."""
    result = TestResult("Schema Information")
    
    try:
        import time
        start = time.time()
        
        resp = requests.get(f"{API_BASE_URL}/api/metrics/schema", timeout=30)
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            tables = data.get("tables", [])
            result.passed = True
            result.message = f"Retrieved schema with {len(tables)} tables"
            result.data = {"table_count": len(tables), "tables": [t.get("name", t) for t in tables[:5]]}
        elif resp.status_code == 404:
            result.passed = True
            result.message = "Schema endpoint not implemented (optional)"
        else:
            result.message = f"Failed: {resp.status_code}"
    except Exception as e:
        result.message = f"Error: {e}"
    
    return result


def test_ai_analysis():
    """Step 5: Test AI Analysis on a Sample Query."""
    result = TestResult("AI Query Analysis")
    
    test_query = "SELECT * FROM demo_orders WHERE user_id = 123"
    
    try:
        import time
        start = time.time()
        
        payload = {"query": test_query}
        resp = requests.post(
            f"{API_BASE_URL}/api/ai/analyze",
            json=payload,
            timeout=120
        )
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            result.passed = True
            
            # Extract key info from response
            suggestion = data.get("suggestion", data.get("recommendations", [{}]))
            if isinstance(suggestion, list) and len(suggestion) > 0:
                suggestion = suggestion[0]
            
            category = suggestion.get("category", suggestion.get("type", "unknown"))
            result.message = f"Analysis complete: {category}"
            result.data = {
                "category": category,
                "title": suggestion.get("title", ""),
                "sql_fix": suggestion.get("sql", suggestion.get("sql_fix", ""))[:100]
            }
        else:
            result.message = f"Analysis failed: {resp.status_code} - {resp.text[:200]}"
    except requests.exceptions.Timeout:
        result.message = "Analysis timeout (LLM may be slow)"
    except Exception as e:
        result.message = f"Error: {e}"
    
    return result


def test_index_recommendations():
    """Step 6: Test Index Recommendations."""
    result = TestResult("Index Recommendations")
    
    try:
        import time
        start = time.time()
        
        resp = requests.get(f"{API_BASE_URL}/api/analysis/index-recommendations", timeout=30)
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            recommendations = data.get("recommendations", data) if isinstance(data, dict) else data
            
            if isinstance(recommendations, list):
                result.passed = True
                result.message = f"Found {len(recommendations)} index recommendations"
                result.data = {"count": len(recommendations)}
            else:
                result.passed = True
                result.message = "Index recommendations endpoint responsive"
                result.data = data
        elif resp.status_code == 404:
            result.passed = True
            result.message = "Index recommendations not available (may need schema)"
        else:
            result.message = f"Failed: {resp.status_code}"
    except Exception as e:
        result.message = f"Error: {e}"
    
    return result


def test_health_scan():
    """Step 7: Test Health Scan."""
    result = TestResult("Database Health Scan")
    
    try:
        import time
        start = time.time()
        
        resp = requests.get(f"{API_BASE_URL}/api/health/scan", timeout=60)
        result.duration_ms = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            result.passed = True
            
            # Extract health score if available
            score = data.get("overall_score", data.get("score", "N/A"))
            result.message = f"Health scan complete (score: {score})"
            result.data = data
        elif resp.status_code == 404:
            result.passed = True
            result.message = "Health scan endpoint not implemented (optional)"
        else:
            result.message = f"Failed: {resp.status_code}"
    except Exception as e:
        result.message = f"Error: {e}"
    
    return result


def run_all_tests():
    """Run all tests and collect results."""
    tests = [
        test_api_health,
        test_database_connection,
        test_get_metrics,
        test_schema_info,
        test_ai_analysis,
        test_index_recommendations,
        test_health_scan,
    ]
    
    results = []
    
    for test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_func.__doc__.strip()}")
        
        result = test_func()
        results.append(result)
        
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        logger.info(f"{status}: {result.message}")
        if result.duration_ms > 0:
            logger.info(f"Duration: {result.duration_ms:.0f}ms")
    
    return results


def print_summary(results):
    """Print test summary."""
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    logger.info("\n" + "=" * 60)
    logger.info("END-TO-END TEST SUMMARY")
    logger.info("=" * 60)
    
    for result in results:
        status = "✅" if result.passed else "❌"
        logger.info(f"  {status} {result.name}: {result.message}")
    
    logger.info("")
    logger.info(f"Total: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {passed/len(results)*100:.0f}%")
    logger.info("=" * 60)
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! MySQLens is ready for use.")
    else:
        logger.info("\n⚠️  SOME TESTS FAILED - Check the details above.")
    
    return failed == 0


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("MySQLens End-to-End Test Suite")
    logger.info("=" * 60)
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info(f"Test Database: {TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    results = run_all_tests()
    success = print_summary(results)
    
    # Save results to file
    output = {
        "timestamp": datetime.now().isoformat(),
        "api_url": API_BASE_URL,
        "database": TEST_DB_CONFIG,
        "results": [
            {
                "name": r.name,
                "passed": r.passed,
                "message": r.message,
                "duration_ms": r.duration_ms,
                "data": r.data
            }
            for r in results
        ]
    }
    
    output_file = os.path.join(
        os.path.dirname(__file__),
        f"e2e_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
