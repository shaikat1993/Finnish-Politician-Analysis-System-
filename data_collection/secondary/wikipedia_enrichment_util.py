from database.neo4j_integration import get_neo4j_writer
from data_collection.secondary.wikipedia_person_collector import WikipediaPersonCollector
import logging

async def enrich_and_store_wikipedia(politician_id: str, politician_name: str):
    """
    Fetch Wikipedia data for a politician and persist to Neo4j.
    Returns a dict with wikipedia_url, wikipedia_summary, wikipedia_image_url.
    """
    logger = logging.getLogger("wikipedia_enrichment_util")
    wiki = WikipediaPersonCollector()
    info = wiki.get_politician_info(politician_name)
    if not info:
        logger.warning(f"No Wikipedia data found for {politician_name}")
        return None
    neo4j_writer = await get_neo4j_writer()
    # Prepare update dict
    update_data = {
    'id': politician_id,
    'name': politician_name,
    'wikipedia_url': info.url,
    'wikipedia_summary': info.summary,
    'wikipedia_image_url': info.image_url,
    }
    await neo4j_writer.create_politician(update_data, source='wikipedia')
    return {
        'url': info.url,
        'summary': info.summary,
        'image_url': info.image_url
    }
