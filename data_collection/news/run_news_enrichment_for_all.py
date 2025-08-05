import sys
import os
import asyncio

# Ensure project root is in sys.path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_collection.news.unified_news_enricher import UnifiedNewsEnricher
from database.neo4j_integration import Neo4jConnectionManager, Neo4jWriter

async def get_all_politicians(session):
    query = "MATCH (p:Politician) RETURN p.id AS id, p.name AS name"
    result = await session.run(query)
    return [record for record in [record async for record in result]]

async def main():
    # Initialize Neo4j connection manager and session
    manager = Neo4jConnectionManager()
    await manager.initialize()
    neo4j_writer = Neo4jWriter(manager)
    await neo4j_writer.initialize()
    async with manager.session() as session:
        politicians = await get_all_politicians(session)
        print(f"Found {len(politicians)} politicians.")
        print("Sample politician dicts:", politicians[:3])
        enricher = UnifiedNewsEnricher(neo4j_writer=neo4j_writer)
        for pol in politicians:
            pol_id = pol['id']
            pol_name = pol['name']
            if not pol_id or not pol_name or str(pol_id).lower() == 'none' or str(pol_name).lower() == 'none':
                print(f"Skipping politician with invalid id or name: id={pol_id}, name={pol_name}")
                continue
            print(f"Enriching news for {pol_name} ({pol_id})...")
            try:
                await enricher.enrich_and_store_politician_news(pol_id, pol_name)
            except Exception as e:
                print(f"Error enriching news for {pol_name}: {e}")
    await manager.close()
    print("News enrichment for all politicians complete.")

if __name__ == "__main__":
    asyncio.run(main())
