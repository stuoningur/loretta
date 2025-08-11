"""
Database abstraction layer for the Loretta project.
Contains models and database management utilities that can be shared
between the Discord bot and the web interface.
"""

from .init import initialize_database
from .manager import DatabaseManager
from .models import (
    Birthday,
    CommandStatistic,
    GuildConfig,
    MemoryTiming,
    Specification,
)

__all__ = [
    "DatabaseManager",
    "Birthday",
    "CommandStatistic",
    "GuildConfig",
    "MemoryTiming",
    "Specification",
    "initialize_database",
]
