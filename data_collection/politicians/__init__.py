"""
Politicians Data Collectors
Contains collectors for official political data sources.
"""

from .eduskunta_collector import EduskuntaCollector
from .vaalikone_collector import VaalikoneCollector
from .kuntaliitto_collector import KuntaliitoCollector

__all__ = [
    'EduskuntaCollector',
    'VaalikoneCollector', 
    'KuntaliitoCollector'
]
