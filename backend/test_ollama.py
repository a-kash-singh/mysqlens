"""
Test script for Ollama provider integration.
Run this to verify your Ollama setup before starting MySQLens.

Usage:
    python test_ollama.py
"""

import asyncio
import sys
from llm.ollama_provider import OllamaProvider
from config import settings


async def test_ollama_connection():
    """Test basic connectivity to Ollama."""
    print("=" * 60)
    print("Testing Ollama Integration for MySQLens")
    print("=" * 60)
    print()

    # Initialize provider
    print(f"📡 Connecting to Ollama at: {settings.ollama_base_url}")
    print(f"🤖 Using model: {settings.ollama_model}")
    print()

    provider = OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model
    )

    # Test 1: Simple generation
    print("Test 1: Simple Text Generation")
    print("-" * 60)
    prompt = "What is a database index? Answer in one sentence."
    print(f"Prompt: {prompt}")
    print("Response: ", end="", flush=True)

    response = await provider.generate(prompt, max_tokens=100)
    print(response)
    print()

    if "Error" in response or "error" in response.lower():
        print("❌ Test 1 FAILED: Could not generate response")
        print()
        print("Troubleshooting:")
        print("1. Make sure Ollama is running: ollama serve")
        print(f"2. Verify the model is installed: ollama list | grep {settings.ollama_model}")
        print(f"3. Pull the model if needed: ollama pull {settings.ollama_model}")
        print(f"4. Test connectivity: curl {settings.ollama_base_url}/api/tags")
        return False
    else:
        print("✅ Test 1 PASSED")
        print()

    # Test 2: JSON analysis
    print("Test 2: JSON-Formatted Analysis")
    print("-" * 60)
    analysis_prompt = """Analyze this SQL query and respond in JSON format:

SELECT * FROM users WHERE email LIKE '%@gmail.com'

Format:
{
    "complexity": "high",
    "issues": ["Full table scan", "Leading wildcard in LIKE"],
    "recommendation": "Add index on email"
}"""

    print("Analyzing a test SQL query...")
    result = await provider.analyze(analysis_prompt, max_tokens=300)
    print("Response:")
    print(result)
    print()

    if isinstance(result, dict) and "error" not in result:
        print("✅ Test 2 PASSED")
        print()
    else:
        print("⚠️  Test 2 WARNING: Could not parse JSON (model may need tuning)")
        print()

    # Test 3: Full recommendation workflow
    print("Test 3: Query Recommendation Workflow")
    print("-" * 60)

    test_query = "SELECT * FROM orders WHERE user_id = 123 AND created_at > '2024-01-01'"
    test_schema = """
    CREATE TABLE orders (
        id INT PRIMARY KEY,
        user_id INT,
        created_at DATETIME,
        total DECIMAL(10,2)
    );
    -- No indexes besides PRIMARY KEY
    """
    test_metrics = {
        "total_time": 5000000,  # 5 seconds in microseconds
        "calls": 1000,
        "mean_time": 5000,
        "rows_examined": 100000,
        "rows_sent": 50,
        "tmp_tables": 0,
        "tmp_disk_tables": 0
    }

    print("Query:", test_query[:60] + "...")
    print("Analyzing with schema context...")

    recommendation = await provider.generate_recommendation(
        query=test_query,
        schema_context=test_schema,
        metrics=test_metrics
    )

    if "error" in recommendation:
        print("❌ Test 3 FAILED:")
        print(recommendation["error"])
        print()
        return False
    else:
        print("✅ Test 3 PASSED")
        print()
        print("Sample recommendation:")
        if "analysis" in recommendation:
            print(f"  Analysis: {recommendation['analysis'][:100]}...")
        if "recommendations" in recommendation and len(recommendation["recommendations"]) > 0:
            print(f"  Found {len(recommendation['recommendations'])} recommendations")
        print()

    # Summary
    print("=" * 60)
    print("✅ All tests passed! Ollama is ready for MySQLens")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start MySQLens: docker-compose up -d")
    print("2. Access dashboard: http://localhost:3000")
    print("3. Connect to your MySQL database")
    print("4. Start getting AI-powered optimization recommendations!")
    print()

    return True


async def check_ollama_availability():
    """Check if Ollama is reachable."""
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    print(f"✅ Ollama is running at {settings.ollama_base_url}")
                    print(f"📦 Installed models: {len(models)}")
                    for model in models:
                        print(f"   - {model.get('name', 'unknown')}")
                    print()
                    return True
                else:
                    print(f"❌ Ollama returned status {response.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print(f"❌ Cannot connect to Ollama at {settings.ollama_base_url}")
        print()
        print("Is Ollama running? Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


async def main():
    """Run all tests."""
    # Check availability first
    available = await check_ollama_availability()
    if not available:
        sys.exit(1)

    # Run tests
    success = await test_ollama_connection()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    print()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
