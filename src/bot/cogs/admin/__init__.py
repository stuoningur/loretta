"""
Admin Cogs für den Loretta Discord Bot
Enthält Administratorfunktionen und Bot-Verwaltung
"""

from . import (
    cog_management,
    command_sync,
    config,
    error_handler,
    member_log,
    picture_only,
    purge,
    shutdown,
)

__all__ = [
    "cog_management",
    "command_sync",
    "config",
    "error_handler",
    "member_log",
    "picture_only",
    "purge",
    "shutdown",
]
