"""
SQL-Schema-Definitionen für das Loretta-Projekt.
Alle Datenbankschemas, Trigger und Indizes sind hier zentralisiert.
"""

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

# SQL-Schema für Command-Statistiken
COMMAND_STATISTICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS command_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    command_name TEXT NOT NULL,
    cog_name TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT
);
"""

# SQL-Schema für Memory-Timings
MEMORY_TIMINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_timings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation TEXT NOT NULL,
    name TEXT NOT NULL,
    rank TEXT,
    vendor TEXT,
    ics TEXT,
    memclk INTEGER,
    fclk INTEGER,
    preset TEXT,
    pdm TEXT,
    gdm TEXT,
    vsoc TEXT,
    vdimm TEXT,
    vdd TEXT,
    vddq TEXT,
    vddio TEXT,
    vddg TEXT,
    cldo_vddp TEXT,
    vddp TEXT,
    cads TEXT,
    procodt TEXT,
    rtts TEXT,
    tcl INTEGER,
    trcdrp INTEGER,
    trcdwr INTEGER,
    trcd INTEGER,
    trp INTEGER,
    tras INTEGER,
    trc INTEGER,
    trrds INTEGER,
    trrdl INTEGER,
    tfaw INTEGER,
    twtrs INTEGER,
    twtrl INTEGER,
    twr INTEGER,
    trdrdscl INTEGER,
    twrwrscl INTEGER,
    trefi INTEGER,
    trfc INTEGER,
    tcwl INTEGER,
    trtp INTEGER,
    trdwr INTEGER,
    twrrd INTEGER,
    twrwrsc INTEGER,
    twrwrsd INTEGER,
    twrwrdd INTEGER,
    trdrdsc INTEGER,
    trdrdsd INTEGER,
    trdrddd INTEGER,
    tcke INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
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

# Indizes für Command-Statistiken-Performance
COMMAND_STATISTICS_INDEXES = [
    # Index für Guild-basierte Abfragen
    "CREATE INDEX IF NOT EXISTS idx_command_stats_guild_id ON command_statistics(guild_id);",
    # Index für Benutzer-basierte Abfragen
    "CREATE INDEX IF NOT EXISTS idx_command_stats_user_id ON command_statistics(user_id);",
    # Index für Command-Name-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_command_stats_command_name ON command_statistics(command_name);",
    # Index für Zeitstempel-basierte Abfragen
    "CREATE INDEX IF NOT EXISTS idx_command_stats_executed_at ON command_statistics(executed_at DESC);",
    # Zusammengesetzter Index für häufige Abfragen
    "CREATE INDEX IF NOT EXISTS idx_command_stats_guild_command ON command_statistics(guild_id, command_name);",
    # Index für Erfolg/Fehler-Filter
    "CREATE INDEX IF NOT EXISTS idx_command_stats_success ON command_statistics(success);",
]

# Indizes für Memory-Timings-Performance
MEMORY_TIMINGS_INDEXES = [
    # Index für Generation-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_generation ON memory_timings(generation);",
    # Index für Hersteller-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_vendor ON memory_timings(vendor);",
    # Index für Speicher-IC-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_ics ON memory_timings(ics);",
    # Index für Speichertakt-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_memclk ON memory_timings(memclk);",
    # Index für FCLK-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_fclk ON memory_timings(fclk);",
    # Zusammengesetzter Index für häufige Suchabfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_search ON memory_timings(generation, vendor, ics);",
    # Index für Preset-Abfragen
    "CREATE INDEX IF NOT EXISTS idx_memory_timings_preset ON memory_timings(preset);",
]
