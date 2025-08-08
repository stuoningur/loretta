"""
Datenbank-Schema-Definitionen für den Loretta Discord-Bot.
"""

import aiosqlite
import logging

logger = logging.getLogger(__name__)

# SQL-Schema für Guild-Konfigurationen
GUILD_CONFIG_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    command_prefix TEXT NOT NULL DEFAULT '!',
    log_channel_id INTEGER,
    news_channel_id INTEGER,
    birthday_channel_id INTEGER,
    picture_only_channels TEXT,  -- JSON-Array von Kanal-IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Trigger um den updated_at Zeitstempel zu aktualisieren
UPDATE_GUILD_CONFIG_TIMESTAMP_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_guild_config_timestamp 
    AFTER UPDATE ON guild_config
    FOR EACH ROW
BEGIN
    UPDATE guild_config SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
END;
"""

# SQL-Schema für RSS-Einträge-Verfolgung
RSS_ENTRIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS posted_rss_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_guid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL-Schema für Geburtstage
BIRTHDAYS_SCHEMA = """
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    birth_day INTEGER NOT NULL CHECK(birth_day >= 1 AND birth_day <= 31),
    birth_month INTEGER NOT NULL CHECK(birth_month >= 1 AND birth_month <= 12),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id)
);
"""


# SQL-Schema für Benutzer-Spezifikationen
SPECIFICATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS specifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    specs_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id)
);
"""

# Trigger um den updated_at Zeitstempel zu aktualisieren for specifications
UPDATE_SPECS_TIMESTAMP_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_specifications_timestamp 
    AFTER UPDATE ON specifications
    FOR EACH ROW
BEGIN
    UPDATE specifications SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""

# Indizes für Performance-Optimierung
SPECIFICATIONS_INDEXES = [
    # Index für Guild-basierte Abfragen (häufigste)
    "CREATE INDEX IF NOT EXISTS idx_specifications_guild_id ON specifications(guild_id);",
    # Zusammengesetzter Index für Suchabfragen (guild_id + Textsuche)
    "CREATE INDEX IF NOT EXISTS idx_specifications_guild_search ON specifications(guild_id, specs_text);",
    # Index für Benutzer-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_specifications_user_id ON specifications(user_id);",
    # Index für updated_at Sortierung
    "CREATE INDEX IF NOT EXISTS idx_specifications_updated_at ON specifications(updated_at DESC);",
]

# Indizes für Geburtstage-Performance
BIRTHDAYS_INDEXES = [
    # Index für Guild-basierte Abfragen
    "CREATE INDEX IF NOT EXISTS idx_birthdays_guild_id ON birthdays(guild_id);",
    # Index für Geburtstags-Matching (Monat/Tag Abfragen)
    "CREATE INDEX IF NOT EXISTS idx_birthdays_date_lookup ON birthdays(guild_id, birth_month, birth_day);",
]


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

            # Übertrage Änderungen
            await db.commit()
            logger.info("Datenbank erfolgreich mit Performance-Indizes initialisiert")

    except Exception as e:
        logger.error(f"Datenbankinitialisierung fehlgeschlagen: {e}")
        raise
