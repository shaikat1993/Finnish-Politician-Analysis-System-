"""
Entrypoint script for running the AI Pipeline Agent Orchestrator in production.
This script can be used as the CMD entrypoint for the Docker container.
"""
import asyncio
import logging
import os
from agent_orchestrator import get_agent_orchestrator

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    orchestrator = get_agent_orchestrator()
    try:
        asyncio.run(orchestrator.initialize())
        print("AgentOrchestrator initialized and ready.")
        # Optionally, keep the orchestrator running or expose a CLI/REST API here
        # For now, just keep the process alive to simulate a service
        while True:
            asyncio.sleep(3600)
    except Exception as e:
        print(f"Failed to initialize AgentOrchestrator: {e}")
        exit(1)
