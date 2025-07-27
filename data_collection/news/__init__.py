"""
News Data Collectors
Contains collectors for Finnish news sources.
"""

from .yle_news_collector import YleNewsCollector
from .helsingin_sanomat_collector import HelsingingSanomatCollector
from .iltalehti_collector import IltalehtCollector
from .mtv_uutiset_collector import MTVUutisetCollector
from .kauppalehti_collector import KauppalehtiCollector

__all__ = [
    'YleNewsCollector',
    'HelsingingSanomatCollector',
    'IltalehtCollector', 
    'MTVUutisetCollector',
    'KauppalehtiCollector'
]
