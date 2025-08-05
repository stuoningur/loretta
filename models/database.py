"""
Database schema definitions for the Loretta Discord bot.
"""

import aiosqlite
import logging

logger = logging.getLogger(__name__)

# SQL schema for server configurations
SERVER_CONFIG_SCHEMA = """
CREATE TABLE IF NOT EXISTS server_config (
    guild_id INTEGER PRIMARY KEY,
    command_prefix TEXT NOT NULL DEFAULT '!',
    log_channel_id INTEGER,
    news_channel_id INTEGER,
    picture_only_channels TEXT,  -- JSON array of channel IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Trigger to update the updated_at timestamp
UPDATE_TIMESTAMP_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_server_config_timestamp 
    AFTER UPDATE ON server_config
    FOR EACH ROW
BEGIN
    UPDATE server_config SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
END;
"""

# SQL schema for RSS entries tracking
RSS_ENTRIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS posted_rss_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_guid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""



async def initialize_database(db_path: str) -> None:
    """
    Initialize the database with the required schema.

    Args:
        db_path: Path to the SQLite database file
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Create server_config table
            await db.execute(SERVER_CONFIG_SCHEMA)

            # Create timestamp update trigger
            await db.execute(UPDATE_TIMESTAMP_TRIGGER)

            # Create RSS entries table
            await db.execute(RSS_ENTRIES_SCHEMA)

            # Commit changes
            await db.commit()
            logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
