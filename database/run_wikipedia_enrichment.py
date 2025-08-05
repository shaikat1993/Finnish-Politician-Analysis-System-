import asyncio
from collector_neo4j_bridge import CollectorNeo4jBridge

async def run():
    bridge = CollectorNeo4jBridge()
    await bridge.initialize()
    print("Starting Wikipedia enrichment for all politicians...")
    result = await bridge._collect_wikipedia_enrichment()
    print("Wikipedia enrichment result:")
    print(result)
    await bridge.close()

if __name__ == "__main__":
    asyncio.run(run())
