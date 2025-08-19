"""
News Data Collectors package

This package intentionally avoids importing heavy collector modules at import time
to keep side effects minimal (e.g., external dependencies like feedparser).

Import collectors explicitly where needed, e.g.:
    from data_collection.news.yle_news_collector import YleNewsCollector
"""

__all__ = [
    'YleNewsCollector',
    'HelsingingSanomatCollector',
    'IltalehtCollector',
    'MTVUutisetCollector',
    'KauppalehtiCollector',
]
