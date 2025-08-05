import asyncio
import logging
from data_collection.news.unified_news_enricher import UnifiedNewsEnricher

# Set up logging to display info-level logs to the console
logging.basicConfig(level=logging.INFO)

async def test_enricher_all_collectors():
    # Use default collectors (includes all: Yle, HS, IL, MTV, Kauppalehti)
    enricher = UnifiedNewsEnricher()
    # In production, this should come from the details API or be passed as an argument
    politician_name = "Ilmari Nurminen"  # Example real Finnish politician
    politician_id = "test_sanna_marin"
    print(f"Testing news enrichment for: {politician_name}")
    articles = await enricher.enrich_and_store_politician_news(
        politician_id=politician_id,
        politician_name=politician_name,
        limit=5
    )
    print(f"Collected {len(articles)} articles.")
    for i, article in enumerate(articles):
        print(f"[{i+1}] {article.get('title', 'No Title')} | {article.get('url', '')}")
    print("\nCollector test complete.")

if __name__ == "__main__":
    asyncio.run(test_enricher_all_collectors())
