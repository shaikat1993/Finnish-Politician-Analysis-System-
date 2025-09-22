"""
Entrypoint script for running the AI Pipeline Agent Orchestrator in production.
This script can be used as the CMD entrypoint for the Docker container.
"""
import asyncio
import logging
import os
from ai_pipeline.agent_orchestrator import get_agent_orchestrator

async def sleep_for(seconds):
    """Async sleep function"""
    await asyncio.sleep(seconds)

async def run_forever():
    """Initialize the orchestrator and keep it running"""
    orchestrator = get_agent_orchestrator()
    await orchestrator.initialize()
    print("AgentOrchestrator initialized and ready.")
    
    # Keep the process alive
    while True:
        await sleep_for(3600)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(run_forever())
    except Exception as e:
        print(f"Failed to run AgentOrchestrator: {e}")
        exit(1)
