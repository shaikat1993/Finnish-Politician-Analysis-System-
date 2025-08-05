import pytest
import asyncio
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_pipeline.agent_orchestrator import get_agent_orchestrator

@pytest.mark.asyncio
async def test_politician_chat_end_to_end():
    """
    End-to-end test for the AI pipeline: simulates chat about a politician and checks agent responses.
    """
    orchestrator = get_agent_orchestrator()
    await orchestrator.initialize()

    # Example politician (replace with one in your DB)
    politician_name = "Sauli Väinämö Niinistö"

    queries = [
        (f"What is the full name of {politician_name}?", ["sauli", "niinistö"]),
        (f"Tell me about {politician_name}'s personal background.", ["born", "birth", "personal", "niinistö"]),
        (f"What is {politician_name}'s academic background?", ["university", "degree", "education", "academic"]),
        (f"Describe {politician_name}'s political career.", ["career", "president", "parliament", "political"]),
        (f"List some key achievements of {politician_name}.", ["achievement", "award", "milestone"]),
    ]

    for query, expected_keywords in queries:
        response = await orchestrator.agents["query"].executor.ainvoke({"input": query})
        assert response is not None, f"No response for: {query}"
        response_text = str(response).lower()
        print(f"\nQuery: {query}\nResponse: {response_text}\n")
        # At least one keyword should be in the response
        assert any(kw in response_text for kw in expected_keywords), f"Response does not contain expected info: {response_text}"

if __name__ == "__main__":
    asyncio.run(test_politician_chat_end_to_end())
