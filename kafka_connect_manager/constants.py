"""constants.py contains necessary constants"""
from enum import Enum


class ConnectorType(str, Enum):
    """Types of connectors"""

    ALL = "all"
    SINK = "sink"
    SOURCE = "source"
