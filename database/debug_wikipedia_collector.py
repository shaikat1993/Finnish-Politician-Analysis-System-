import asyncio
from collector_neo4j_bridge import get_neo4j_manager
from data_collection.secondary.wikipedia_collector import WikipediaCollector

async def get_politician_names(limit=25):
    manager = await get_neo4j_manager()
    # Get a sample of politician names
    records = await manager.execute_query(
        "MATCH (p:Politician) RETURN p.name as name, p.politician_id as id LIMIT $limit",
        {"limit": limit}
    )
    return [(r['name'], r['id']) for r in records]

async def main():
    names = await get_politician_names(25)
    wc = WikipediaCollector()
    print("Testing WikipediaCollector.get_politician_info on real names from Neo4j:\n")
    for name, pid in names:
        print(f"Testing: {name} (ID: {pid})")
        try:
            result = wc.get_politician_info(name)
            if result:
                print(f"  SUCCESS: Found Wikipedia page: {result.url}")
                print(f"    Summary: {result.summary[:120]}...")
                print(f"    Image: {result.image_url}")
            else:
                print("  FAIL: No Wikipedia page found.")
        except Exception as e:
            print(f"  ERROR: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
