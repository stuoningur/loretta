"""
Datenbankinitialisierung für das Loretta-Projekt.
"""

import logging

import aiosqlite

from .schemas import (
    BIRTHDAYS_INDEXES,
    BIRTHDAYS_SCHEMA,
    COMMAND_STATISTICS_INDEXES,
    COMMAND_STATISTICS_SCHEMA,
    GUILD_CONFIG_SCHEMA,
    MEMORY_TIMINGS_INDEXES,
    MEMORY_TIMINGS_SCHEMA,
    RSS_ENTRIES_SCHEMA,
    SPECIFICATIONS_INDEXES,
    SPECIFICATIONS_SCHEMA,
    UPDATE_GUILD_CONFIG_TIMESTAMP_TRIGGER,
    UPDATE_SPECS_TIMESTAMP_TRIGGER,
)

logger = logging.getLogger(__name__)


async def initialize_database(db_path: str) -> None:
    """
    Initialisiert die Datenbank mit dem erforderlichen Schema.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Erstelle guild_config Tabelle
            await db.execute(GUILD_CONFIG_SCHEMA)

            # Erstelle Zeitstempel-Update-Trigger
            await db.execute(UPDATE_GUILD_CONFIG_TIMESTAMP_TRIGGER)

            # Erstelle RSS-Einträge Tabelle
            await db.execute(RSS_ENTRIES_SCHEMA)

            # Erstelle Geburtstags-Tabelle
            await db.execute(BIRTHDAYS_SCHEMA)

            # Erstelle Spezifikations-Tabelle
            await db.execute(SPECIFICATIONS_SCHEMA)

            # Erstelle Spezifikations-Zeitstempel-Update-Trigger
            await db.execute(UPDATE_SPECS_TIMESTAMP_TRIGGER)

            # Erstelle Performance-Indizes für Spezifikationen
            for index_sql in SPECIFICATIONS_INDEXES:
                await db.execute(index_sql)

            # Erstelle Performance-Indizes für Geburtstage
            for index_sql in BIRTHDAYS_INDEXES:
                await db.execute(index_sql)

            # Erstelle Command-Statistiken-Tabelle
            await db.execute(COMMAND_STATISTICS_SCHEMA)

            # Erstelle Performance-Indizes für Command-Statistiken
            for index_sql in COMMAND_STATISTICS_INDEXES:
                await db.execute(index_sql)

            # Erstelle Memory-Timings-Tabelle
            await db.execute(MEMORY_TIMINGS_SCHEMA)

            # Erstelle Performance-Indizes für Memory-Timings
            for index_sql in MEMORY_TIMINGS_INDEXES:
                await db.execute(index_sql)

            # Übertrage Änderungen
            await db.commit()
            logger.info("Datenbank erfolgreich mit Performance-Indizes initialisiert")

    except Exception as e:
        logger.error(f"Datenbankinitialisierung fehlgeschlagen: {e}")
        raise
