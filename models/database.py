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

# SQL schema for birthdays
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

# SQL schema for birthday channels
BIRTHDAY_CHANNELS_SCHEMA = """
CREATE TABLE IF NOT EXISTS birthday_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, channel_id)
);
"""

# SQL schema for user specifications
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

# Trigger to update the updated_at timestamp for specifications
UPDATE_SPECS_TIMESTAMP_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_specifications_timestamp 
    AFTER UPDATE ON specifications
    FOR EACH ROW
BEGIN
    UPDATE specifications SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""

# Indexes for performance optimization
SPECIFICATIONS_INDEXES = [
    # Index for guild-based queries (most common)
    "CREATE INDEX IF NOT EXISTS idx_specifications_guild_id ON specifications(guild_id);",
    # Composite index for search queries (guild_id + text search)
    "CREATE INDEX IF NOT EXISTS idx_specifications_guild_search ON specifications(guild_id, specs_text);",
    # Index for user lookups
    "CREATE INDEX IF NOT EXISTS idx_specifications_user_id ON specifications(user_id);",
    # Index for updated_at ordering
    "CREATE INDEX IF NOT EXISTS idx_specifications_updated_at ON specifications(updated_at DESC);",
]


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

            # Create birthdays table
            await db.execute(BIRTHDAYS_SCHEMA)

            # Create birthday channels table
            await db.execute(BIRTHDAY_CHANNELS_SCHEMA)

            # Create specifications table
            await db.execute(SPECIFICATIONS_SCHEMA)

            # Create specifications timestamp update trigger
            await db.execute(UPDATE_SPECS_TIMESTAMP_TRIGGER)

            # Create performance indexes
            for index_sql in SPECIFICATIONS_INDEXES:
                await db.execute(index_sql)

            # Commit changes
            await db.commit()
            logger.info("Database initialized successfully with performance indexes")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
