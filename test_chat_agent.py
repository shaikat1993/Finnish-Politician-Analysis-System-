#!/usr/bin/env python3
"""
Test script to verify chat agent works with updated max_iterations
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_pipeline.agent_orchestrator import AgentOrchestrator

async def test_chat_agent():
    """Test the chat agent with a simple query"""

    print("🔧 Initializing AgentOrchestrator...")
    orchestrator = AgentOrchestrator()
    await orchestrator.initialize()

    print("✅ AgentOrchestrator initialized successfully")
    print(f"   - Query Agent max_iterations: {orchestrator.agents['query'].executor.max_iterations}")
    print(f"   - Analysis Agent max_iterations: {orchestrator.agents['analysis'].executor.max_iterations}")

    # Simple test query
    test_query = "What is the capital of Finland?"

    print(f"\n📝 Testing query: '{test_query}'")
    print("⏳ Processing...")

    try:
        result = await orchestrator.process_user_query(
            query=test_query,
            context=None
        )

        print("\n✅ Query completed successfully!")
        print(f"\n📊 Result:")
        print(f"   Answer: {result.get('answer', 'N/A')[:200]}...")
        print(f"   Agent: {result.get('agent_used', 'N/A')}")
        print(f"   Response time: {result.get('response_time', 'N/A')}")

        # Check permission metrics
        query_metrics = orchestrator.agents['query'].executor.get_permission_metrics()
        print(f"\n🔒 Permission Metrics:")
        print(f"   Total requests: {query_metrics.get('total_requests', 0)}")
        print(f"   Allowed: {query_metrics.get('allowed_count', 0)}")
        print(f"   Denied: {query_metrics.get('denied_count', 0)}")

        return True

    except Exception as e:
        print(f"\n❌ Error during query processing:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio

    print("=" * 60)
    print("Chat Agent Test Script")
    print("Testing updated max_iterations and SecureAgentExecutor")
    print("=" * 60)
    print()

    success = asyncio.run(test_chat_agent())

    print()
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed - see errors above")
    print("=" * 60)

    sys.exit(0 if success else 1)
