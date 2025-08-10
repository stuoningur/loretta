"""
Datenbank-Utility-Funktionen für Guild-Konfigurationsverwaltung.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple, Union

import aiosqlite
import discord

logger = logging.getLogger(__name__)


@dataclass
class GuildConfig:
    """Datenklasse für Guild-Konfiguration."""

    guild_id: int
    command_prefix: str = "!"
    log_channel_id: Optional[int] = None
    news_channel_id: Optional[int] = None
    birthday_channel_id: Optional[int] = None
    picture_only_channels: List[int] = field(default_factory=list)


# Backward compatibility alias
ServerConfig = GuildConfig


@dataclass
class Birthday:
    """Datenklasse für Benutzer-Geburtstag."""

    id: Optional[int]
    guild_id: int
    user_id: int
    birth_day: int
    birth_month: int


@dataclass
class Specification:
    """Datenklasse für Benutzer-Spezifikationen."""

    id: Optional[int]
    guild_id: int
    user_id: int
    specs_text: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CommandStatistic:
    """Datenklasse für Command-Statistiken."""

    id: Optional[int]
    guild_id: int
    user_id: int
    command_name: str
    cog_name: Optional[str] = None
    executed_at: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class MemoryTiming:
    """Datenklasse für Memory-Timings."""

    id: Optional[int]
    generation: str
    name: str
    rank: Optional[str] = None
    vendor: Optional[str] = None
    ics: Optional[str] = None
    memclk: Optional[int] = None
    fclk: Optional[int] = None
    preset: Optional[str] = None
    pdm: Optional[str] = None
    gdm: Optional[str] = None
    vsoc: Optional[str] = None
    vdimm: Optional[str] = None
    vdd: Optional[str] = None
    vddq: Optional[str] = None
    vddio: Optional[str] = None
    vddg: Optional[str] = None
    cldo_vddp: Optional[str] = None
    vddp: Optional[str] = None
    cads: Optional[str] = None
    procodt: Optional[str] = None
    rtts: Optional[str] = None
    tcl: Optional[int] = None
    trcdrp: Optional[int] = None
    trcdwr: Optional[int] = None
    trcd: Optional[int] = None
    trp: Optional[int] = None
    tras: Optional[int] = None
    trc: Optional[int] = None
    trrds: Optional[int] = None
    trrdl: Optional[int] = None
    tfaw: Optional[int] = None
    twtrs: Optional[int] = None
    twtrl: Optional[int] = None
    twr: Optional[int] = None
    trdrdscl: Optional[int] = None
    twrwrscl: Optional[int] = None
    trefi: Optional[int] = None
    trfc: Optional[int] = None
    tcwl: Optional[int] = None
    trtp: Optional[int] = None
    trdwr: Optional[int] = None
    twrrd: Optional[int] = None
    twrwrsc: Optional[int] = None
    twrwrsd: Optional[int] = None
    twrwrdd: Optional[int] = None
    trdrdsc: Optional[int] = None
    trdrdsd: Optional[int] = None
    trdrddd: Optional[int] = None
    tcke: Optional[int] = None
    created_at: Optional[str] = None


class DatabaseManager:
    """Manager-Klasse für Datenbankoperationen."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get_guild_config(self, guild_id: int) -> GuildConfig:
        """
        Holt die Guild-Konfiguration für eine Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            GuildConfig-Objekt mit der Guild-Konfiguration
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, news_channel_id, birthday_channel_id, picture_only_channels "
                    "FROM guild_config WHERE guild_id = ?",
                    (guild_id,),
                )
                row = await cursor.fetchone()

                if row:
                    picture_only_channels = json.loads(row[5]) if row[5] else []
                    return GuildConfig(
                        guild_id=row[0],
                        command_prefix=row[1],
                        log_channel_id=row[2],
                        news_channel_id=row[3],
                        birthday_channel_id=row[4],
                        picture_only_channels=picture_only_channels,
                    )
                else:
                    # Gib Standard-Konfiguration für neue Guilds zurück
                    return GuildConfig(guild_id=guild_id)

        except Exception as e:
            logger.error(
                f"Fehler beim Abrufen der Guild-Konfiguration für Guild {guild_id}: {e}"
            )
            # Gib Standard-Konfiguration bei Fehler zurück
            return GuildConfig(guild_id=guild_id)

    async def set_guild_config(
        self, config: GuildConfig, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Setzt die Guild-Konfiguration für eine Guild.

        Args:
            config: GuildConfig-Objekt mit der neuen Konfiguration
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            picture_only_json = json.dumps(config.picture_only_channels)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO guild_config
                       (guild_id, command_prefix, log_channel_id, news_channel_id, birthday_channel_id, picture_only_channels)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        config.guild_id,
                        config.command_prefix,
                        config.log_channel_id,
                        config.news_channel_id,
                        config.birthday_channel_id,
                        picture_only_json,
                    ),
                )
                await db.commit()

            guild_info = (
                f"{guild.name} ({config.guild_id})" if guild else str(config.guild_id)
            )
            logger.info(f"Guild-Konfiguration für Guild {guild_info} aktualisiert")
            return True

        except Exception as e:
            guild_info = (
                f"{guild.name} ({config.guild_id})" if guild else str(config.guild_id)
            )
            logger.error(
                f"Fehler beim Setzen der Guild-Konfiguration für Guild {guild_info}: {e}"
            )
            return False

    async def set_command_prefix(
        self, guild_id: int, prefix: str, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Setzt das Command-Prefix für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            prefix: Neues Command-Prefix
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            config.command_prefix = prefix
            return await self.set_guild_config(config, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Setzen des Command-Prefix für Guild {guild_info}: {e}"
            )
            return False

    async def set_log_channel(
        self,
        guild_id: int,
        channel_id: Optional[int],
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Setzt den Log-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID für Logging, None zum Deaktivieren
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            config.log_channel_id = channel_id
            return await self.set_guild_config(config, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Setzen des Log-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def set_news_channel(
        self,
        guild_id: int,
        channel_id: Optional[int],
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Setzt den News-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID für News, None zum Deaktivieren
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            config.news_channel_id = channel_id
            return await self.set_guild_config(config, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Setzen des News-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def add_picture_only_channel(
        self, guild_id: int, channel_id: int, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Fügt einen Kanal zur Liste der Nur-Bild-Kanäle hinzu.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID zum Hinzufügen
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            if channel_id not in config.picture_only_channels:
                config.picture_only_channels.append(channel_id)
                return await self.set_guild_config(config, guild)
            return True

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Hinzufügen des Nur-Bild-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def remove_picture_only_channel(
        self, guild_id: int, channel_id: int, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Entfernt einen Kanal aus der Liste der Nur-Bild-Kanäle.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID zum Entfernen
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            if channel_id in config.picture_only_channels:
                config.picture_only_channels.remove(channel_id)
                return await self.set_guild_config(config, guild)
            return True

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Entfernen des Nur-Bild-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def is_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Überprüft ob ein Kanal als Nur-Bild-Kanal konfiguriert ist.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID zum Überprüfen

        Returns:
            True wenn Kanal Nur-Bild-Kanal ist, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            return channel_id in config.picture_only_channels

        except Exception as e:
            logger.error(
                f"Fehler beim Überprüfen des Nur-Bild-Kanals für Guild {guild_id}: {e}"
            )
            return False

    async def get_all_guild_configs(self) -> List[GuildConfig]:
        """
        Holt alle Guild-Konfigurationen.

        Returns:
            Liste von GuildConfig-Objekten
        """
        try:
            configs = []
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, news_channel_id, birthday_channel_id, picture_only_channels "
                    "FROM guild_config"
                )
                rows = await cursor.fetchall()

                for row in rows:
                    picture_only_channels = json.loads(row[5]) if row[5] else []
                    configs.append(
                        GuildConfig(
                            guild_id=row[0],
                            command_prefix=row[1],
                            log_channel_id=row[2],
                            news_channel_id=row[3],
                            birthday_channel_id=row[4],
                            picture_only_channels=picture_only_channels,
                        )
                    )

            return configs

        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Guild-Konfigurationen: {e}")
            return []

    # Software Check Methoden

    async def is_rss_entry_posted(self, entry_guid: str) -> bool:
        """
        Überprüft ob ein RSS-Eintrag bereits gepostet wurde.

        Args:
            entry_guid: Eindeutige Kennung für den RSS-Eintrag

        Returns:
            True wenn Eintrag bereits gepostet, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM posted_rss_entries WHERE entry_guid = ?",
                    (entry_guid,),
                )
                result = await cursor.fetchone()
                return result is not None

        except Exception as e:
            logger.error(f"Fehler beim Überprüfen des RSS-Eintrags: {e}")
            return True  # Gib True bei Fehler zurück um Spam zu vermeiden

    async def mark_rss_entry_as_posted(
        self, entry_guid: str, title: str, link: str
    ) -> bool:
        """
        Markiert einen RSS-Eintrag als gepostet.

        Args:
            entry_guid: Eindeutige Kennung für den RSS-Eintrag
            title: Eintrag-Titel
            link: Eintrag-Link

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO posted_rss_entries (entry_guid, title, link) VALUES (?, ?, ?)",
                    (entry_guid, title, link),
                )
                await db.commit()
                logger.debug(f"RSS-Eintrag als gepostet markiert: {title}")
                return True

        except Exception as e:
            logger.error(f"Fehler beim Markieren des RSS-Eintrags als gepostet: {e}")
            return False

    async def get_news_channels(self) -> List[int]:
        """
        Holt alle konfigurierten News-Kanäle.

        Returns:
            Liste von Kanal-IDs mit konfigurierten News-Kanälen
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT news_channel_id FROM guild_config WHERE news_channel_id IS NOT NULL"
                )
                results = await cursor.fetchall()
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der News-Kanäle: {e}")
            return []

    # Geburtstags-Verwaltungs-Methoden

    async def add_birthday(
        self,
        birthday: Birthday,
        guild: Optional[discord.Guild] = None,
        user: Optional[Union[discord.User, discord.Member]] = None,
    ) -> bool:
        """
        Fügt einen Benutzer-Geburtstag hinzu oder aktualisiert ihn.

        Args:
            birthday: Birthday-Objekt mit Benutzer-Geburtstagsinformationen
            guild: Discord Guild Objekt für bessere Logs (optional)
            user: Discord User/Member Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO birthdays
                       (guild_id, user_id, birth_day, birth_month)
                       VALUES (?, ?, ?, ?)""",
                    (
                        birthday.guild_id,
                        birthday.user_id,
                        birthday.birth_day,
                        birthday.birth_month,
                    ),
                )
                await db.commit()

            user_info = (
                f"{user.name} ({birthday.user_id})" if user else str(birthday.user_id)
            )
            guild_info = (
                f"{guild.name} ({birthday.guild_id})"
                if guild
                else str(birthday.guild_id)
            )
            logger.info(
                f"Geburtstag für Benutzer {user_info} in Guild {guild_info} hinzugefügt"
            )
            return True

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Geburtstags: {e}")
            return False

    async def remove_birthday(
        self,
        guild_id: int,
        user_id: int,
        guild: Optional[discord.Guild] = None,
        user: Optional[Union[discord.User, discord.Member]] = None,
    ) -> bool:
        """
        Entfernt einen Benutzer-Geburtstag.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID
            guild: Discord Guild Objekt für bessere Logs (optional)
            user: Discord User/Member Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                )
                await db.commit()

            user_info = f"{user.name} ({user_id})" if user else str(user_id)
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.info(
                f"Geburtstag für Benutzer {user_info} in Guild {guild_info} entfernt"
            )
            return True

        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Geburtstags: {e}")
            return False

    async def get_birthday(self, guild_id: int, user_id: int) -> Optional[Birthday]:
        """
        Holt einen Benutzer-Geburtstag.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID

        Returns:
            Birthday-Objekt falls gefunden, None andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, guild_id, user_id, birth_day, birth_month "
                    "FROM birthdays WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                )
                row = await cursor.fetchone()

                if row:
                    return Birthday(
                        id=row[0],
                        guild_id=row[1],
                        user_id=row[2],
                        birth_day=row[3],
                        birth_month=row[4],
                    )
                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Geburtstags: {e}")
            return None

    async def get_birthdays_today(self) -> List[Birthday]:
        """
        Holt alle Geburtstage für heute über alle Guilds hinweg.

        Returns:
            Liste von Birthday-Objekten für Benutzer mit Geburtstag heute
        """
        try:
            today = date.today()
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, guild_id, user_id, birth_day, birth_month "
                    "FROM birthdays WHERE birth_day = ? AND birth_month = ?",
                    (today.day, today.month),
                )
                rows = await cursor.fetchall()

                birthdays = []
                for row in rows:
                    birthdays.append(
                        Birthday(
                            id=row[0],
                            guild_id=row[1],
                            user_id=row[2],
                            birth_day=row[3],
                            birth_month=row[4],
                        )
                    )

                return birthdays

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der heutigen Geburtstage: {e}")
            return []

    async def get_guild_birthdays(self, guild_id: int) -> List[Birthday]:
        """
        Holt alle Geburtstage für eine bestimmte Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            Liste von Birthday-Objekten für die Guild
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, guild_id, user_id, birth_day, birth_month "
                    "FROM birthdays WHERE guild_id = ? "
                    "ORDER BY birth_month, birth_day",
                    (guild_id,),
                )
                rows = await cursor.fetchall()

                birthdays = []
                for row in rows:
                    birthdays.append(
                        Birthday(
                            id=row[0],
                            guild_id=row[1],
                            user_id=row[2],
                            birth_day=row[3],
                            birth_month=row[4],
                        )
                    )

                return birthdays

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Guild-Geburtstage: {e}")
            return []

    async def set_birthday_channel(
        self,
        guild_id: int,
        channel_id: Optional[int],
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Setzt den Geburtstags-Ankündigungs-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Discord Kanal-ID, None zum Deaktivieren
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            config.birthday_channel_id = channel_id
            return await self.set_guild_config(config, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Setzen des Geburtstags-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def remove_birthday_channel(
        self, guild_id: int, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Entfernt den Geburtstags-Ankündigungs-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            return await self.set_birthday_channel(guild_id, None, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Entfernen des Geburtstags-Kanals für Guild {guild_info}: {e}"
            )
            return False

    async def get_birthday_channel(self, guild_id: int) -> Optional[int]:
        """
        Holt den Geburtstags-Ankündigungs-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            Kanal-ID wenn gesetzt, None andernfalls
        """
        try:
            config = await self.get_guild_config(guild_id)
            return config.birthday_channel_id

        except Exception as e:
            logger.error(
                f"Fehler beim Abrufen des Geburtstags-Kanals für Guild {guild_id}: {e}"
            )
            return None

    async def get_all_birthday_channels(self) -> List[Tuple[int, int]]:
        """
        Holt alle Geburtstags-Ankündigungs-Kanäle über alle Guilds hinweg.

        Returns:
            Liste von Tupeln (guild_id, channel_id)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, birthday_channel_id FROM guild_config WHERE birthday_channel_id IS NOT NULL"
                )
                rows = await cursor.fetchall()
                return [(row[0], row[1]) for row in rows]

        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Geburtstags-Kanäle: {e}")
            return []

    async def add_birthday_channel(
        self, guild_id: int, channel_id: int, guild: Optional[discord.Guild] = None
    ) -> bool:
        """
        Fügt einen Geburtstags-Ankündigungs-Kanal für eine Guild hinzu.
        Alias für set_birthday_channel für Rückwärtskompatibilität.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Discord Kanal-ID für Geburtstags-Ankündigungen
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            return await self.set_birthday_channel(guild_id, channel_id, guild)

        except Exception as e:
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)
            logger.error(
                f"Fehler beim Hinzufügen des Geburtstags-Kanals für Guild {guild_info}: {e}"
            )
            return False

    # Spezifikations-Methoden

    async def add_specification(
        self,
        specification: Specification,
        user: Optional[Union[discord.User, discord.Member]] = None,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Fügt Benutzer-Spezifikationen hinzu oder aktualisiert sie.

        Args:
            specification: Specification-Objekt mit den Daten
            user: Discord User/Member Objekt für bessere Logs (optional)
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Prüfe zuerst ob die Spezifikation bereits existiert
                cursor = await db.execute(
                    "SELECT id FROM specifications WHERE guild_id = ? AND user_id = ?",
                    (specification.guild_id, specification.user_id),
                )
                existing = await cursor.fetchone()

                if existing:
                    # Aktualisiere existierenden Eintrag (Trigger wird updated_at aktualisieren)
                    await db.execute(
                        "UPDATE specifications SET specs_text = ? WHERE guild_id = ? AND user_id = ?",
                        (
                            specification.specs_text,
                            specification.guild_id,
                            specification.user_id,
                        ),
                    )
                else:
                    # Füge neuen Eintrag ein (sowohl created_at als auch updated_at werden auf aktuelle Zeit gesetzt)
                    await db.execute(
                        "INSERT INTO specifications (guild_id, user_id, specs_text) VALUES (?, ?, ?)",
                        (
                            specification.guild_id,
                            specification.user_id,
                            specification.specs_text,
                        ),
                    )

                await db.commit()

            # Erstelle aussagekräftige Log-Nachricht
            user_info = (
                f"{user.name} ({specification.user_id})"
                if user
                else str(specification.user_id)
            )
            guild_info = (
                f"{guild.name} ({specification.guild_id})"
                if guild
                else str(specification.guild_id)
            )

            logger.info(
                f"Spezifikationen für Benutzer {user_info} in Guild {guild_info} hinzugefügt/aktualisiert"
            )
            return True

        except Exception as e:
            logger.error(
                f"Fehler beim Hinzufügen/Aktualisieren der Spezifikationen: {e}"
            )
            return False

    async def get_specification(
        self, guild_id: int, user_id: int
    ) -> Optional[Specification]:
        """
        Holt die Spezifikationen eines Benutzers.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID

        Returns:
            Specification-Objekt falls gefunden, None andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, guild_id, user_id, specs_text, created_at, updated_at "
                    "FROM specifications WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                )
                row = await cursor.fetchone()

                if row:
                    return Specification(
                        id=row[0],
                        guild_id=row[1],
                        user_id=row[2],
                        specs_text=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                    )
                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Spezifikation: {e}")
            return None

    async def remove_specification(
        self,
        guild_id: int,
        user_id: int,
        user: Optional[Union[discord.User, discord.Member]] = None,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Entfernt die Spezifikationen eines Benutzers.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID
            user: Discord User/Member Objekt für bessere Logs (optional)
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM specifications WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                )
                await db.commit()

            # Erstelle aussagekräftige Log-Nachricht
            user_info = f"{user.name} ({user_id})" if user else str(user_id)
            guild_info = f"{guild.name} ({guild_id})" if guild else str(guild_id)

            logger.info(
                f"Spezifikationen für Benutzer {user_info} in Guild {guild_info} entfernt"
            )
            return True

        except Exception as e:
            logger.error(f"Fehler beim Entfernen der Spezifikation: {e}")
            return False

    async def search_specifications(
        self, guild_id: int, search_term: str, limit: int = 50, offset: int = 0
    ) -> tuple[List[tuple], int]:
        """
        Sucht nach Hardware in allen Spezifikationen einer Guild mit Paginierung.

        Args:
            guild_id: Discord Guild-ID
            search_term: Hardware-Begriff nach dem gesucht werden soll
            limit: Maximale Anzahl von Rückgabe-Ergebnissen
            offset: Anzahl der zu überspringenden Ergebnisse (für Paginierung)

        Returns:
            Tupel aus (results, total_count) wobei:
            - results: Liste von Tupeln (user_id, specs_text) die dem Suchbegriff entsprechen
            - total_count: Gesamtanzahl der Übereinstimmungen ohne Paginierung
        """
        logger.info(
            f"Datenbanksuche: guild_id={guild_id}, search_term='{search_term}', limit={limit}, offset={offset}"
        )
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Hole zuerst die Gesamtanzahl für Paginierungs-Informationen
                count_cursor = await db.execute(
                    "SELECT COUNT(*) FROM specifications "
                    "WHERE guild_id = ? AND specs_text LIKE ? COLLATE NOCASE",
                    (guild_id, f"%{search_term}%"),
                )
                count_result = await count_cursor.fetchone()
                total_count = count_result[0] if count_result else 0

                # Hole dann die paginierten Ergebnisse
                cursor = await db.execute(
                    "SELECT user_id, specs_text FROM specifications "
                    "WHERE guild_id = ? AND specs_text LIKE ? COLLATE NOCASE "
                    "ORDER BY updated_at DESC "
                    "LIMIT ? OFFSET ?",
                    (guild_id, f"%{search_term}%", limit, offset),
                )
                rows = await cursor.fetchall()
                results = [(row[0], row[1]) for row in rows]
                logger.info(
                    f"Datenbanksuche gab {len(results)} Ergebnisse zurück (Seite {offset // limit + 1}, insgesamt: {total_count})"
                )
                return results, total_count

        except Exception as e:
            logger.error(
                f"Fehler beim Durchsuchen der Spezifikationen: {e}", exc_info=True
            )
            return [], 0

    async def get_all_guild_specifications(self, guild_id: int) -> List[Specification]:
        """
        Holt alle Spezifikationen für eine Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            Liste von Specification-Objekten für die Guild
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, guild_id, user_id, specs_text, created_at, updated_at "
                    "FROM specifications WHERE guild_id = ? "
                    "ORDER BY updated_at DESC",
                    (guild_id,),
                )
                rows = await cursor.fetchall()

                specifications = []
                for row in rows:
                    specifications.append(
                        Specification(
                            id=row[0],
                            guild_id=row[1],
                            user_id=row[2],
                            specs_text=row[3],
                            created_at=row[4],
                            updated_at=row[5],
                        )
                    )

                return specifications

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Guild-Spezifikationen: {e}")
            return []

    # Command-Statistiken-Methoden

    async def log_command_usage(
        self,
        stat: CommandStatistic,
        user: Optional[Union[discord.User, discord.Member]] = None,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        """
        Protokolliert eine Command-Ausführung in der Statistik-Tabelle.

        Args:
            stat: CommandStatistic-Objekt mit den Ausführungsdetails
            user: Discord User/Member Objekt für bessere Logs (optional)
            guild: Discord Guild Objekt für bessere Logs (optional)

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT INTO command_statistics
                       (guild_id, user_id, command_name, cog_name, success, error_message)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        stat.guild_id,
                        stat.user_id,
                        stat.command_name,
                        stat.cog_name,
                        stat.success,
                        stat.error_message,
                    ),
                )
                await db.commit()

            return True

        except Exception as e:
            user_info = f"{user.name} ({stat.user_id})" if user else str(stat.user_id)
            guild_info = (
                f"{guild.name} ({stat.guild_id})" if guild else str(stat.guild_id)
            )
            logger.error(
                f"Fehler beim Protokollieren der Command-Statistik für Benutzer {user_info} in Guild {guild_info}: {e}"
            )
            return False

    async def get_command_statistics_summary(
        self, guild_id: int, days: int = 30
    ) -> dict:
        """
        Holt eine Zusammenfassung der Command-Statistiken für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            days: Anzahl der Tage zurück (Standard: 30)

        Returns:
            Dictionary mit Statistik-Zusammenfassung
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Gesamtanzahl Commands
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_statistics WHERE guild_id = ? AND executed_at >= date('now', '-' || ? || ' days')",
                    (guild_id, days),
                )
                result = await cursor.fetchone()
                total_commands = result[0] if result else 0

                # Erfolgreiche Commands
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_statistics WHERE guild_id = ? AND success = 1 AND executed_at >= date('now', '-' || ? || ' days')",
                    (guild_id, days),
                )
                result = await cursor.fetchone()
                successful_commands = result[0] if result else 0

                # Top Commands
                cursor = await db.execute(
                    """SELECT command_name, COUNT(*) as count
                       FROM command_statistics
                       WHERE guild_id = ? AND executed_at >= date('now', '-' || ? || ' days')
                       GROUP BY command_name
                       ORDER BY count DESC
                       LIMIT 10""",
                    (guild_id, days),
                )
                top_commands = await cursor.fetchall()

                # Top Users
                cursor = await db.execute(
                    """SELECT user_id, COUNT(*) as count
                       FROM command_statistics
                       WHERE guild_id = ? AND executed_at >= date('now', '-' || ? || ' days')
                       GROUP BY user_id
                       ORDER BY count DESC
                       LIMIT 10""",
                    (guild_id, days),
                )
                top_users = await cursor.fetchall()

                return {
                    "total_commands": total_commands,
                    "successful_commands": successful_commands,
                    "failed_commands": total_commands - successful_commands,
                    "success_rate": (
                        (successful_commands / total_commands * 100)
                        if total_commands > 0
                        else 0
                    ),
                    "top_commands": [(row[0], row[1]) for row in top_commands],
                    "top_users": [(row[0], row[1]) for row in top_users],
                    "days": days,
                }

        except Exception as e:
            logger.error(
                f"Fehler beim Abrufen der Command-Statistiken-Zusammenfassung: {e}"
            )
            return {
                "total_commands": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "success_rate": 0,
                "top_commands": [],
                "top_users": [],
                "days": days,
            }

    async def get_user_command_statistics(
        self, guild_id: int, user_id: int, days: int = 30
    ) -> dict:
        """
        Holt Command-Statistiken für einen spezifischen Benutzer.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID
            days: Anzahl der Tage zurück (Standard: 30)

        Returns:
            Dictionary mit Benutzer-Statistiken
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Gesamtanzahl Commands des Benutzers
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_statistics WHERE guild_id = ? AND user_id = ? AND executed_at >= date('now', '-' || ? || ' days')",
                    (guild_id, user_id, days),
                )
                result = await cursor.fetchone()
                total_commands = result[0] if result else 0

                # Erfolgreiche Commands
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM command_statistics WHERE guild_id = ? AND user_id = ? AND success = 1 AND executed_at >= date('now', '-' || ? || ' days')",
                    (guild_id, user_id, days),
                )
                result = await cursor.fetchone()
                successful_commands = result[0] if result else 0

                # Commands des Benutzers
                cursor = await db.execute(
                    """SELECT command_name, COUNT(*) as count
                       FROM command_statistics
                       WHERE guild_id = ? AND user_id = ? AND executed_at >= date('now', '-' || ? || ' days')
                       GROUP BY command_name
                       ORDER BY count DESC""",
                    (guild_id, user_id, days),
                )
                user_commands = await cursor.fetchall()

                # Rang des Benutzers im Server
                cursor = await db.execute(
                    """SELECT user_id, COUNT(*) as count
                       FROM command_statistics
                       WHERE guild_id = ? AND executed_at >= date('now', '-' || ? || ' days')
                       GROUP BY user_id
                       ORDER BY count DESC""",
                    (guild_id, days),
                )
                all_users = await cursor.fetchall()
                user_rank = None
                for i, (uid, _) in enumerate(all_users, 1):
                    if uid == user_id:
                        user_rank = i
                        break

                return {
                    "total_commands": total_commands,
                    "successful_commands": successful_commands,
                    "failed_commands": total_commands - successful_commands,
                    "success_rate": (
                        (successful_commands / total_commands * 100)
                        if total_commands > 0
                        else 0
                    ),
                    "commands_used": [(row[0], row[1]) for row in user_commands],
                    "server_rank": user_rank,
                    "total_server_users": len(list(all_users)),
                    "days": days,
                }

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Benutzer-Command-Statistiken: {e}")
            return {
                "total_commands": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "success_rate": 0,
                "commands_used": [],
                "server_rank": None,
                "total_server_users": 0,
                "days": days,
            }

    # Memory-Timing-Verwaltungs-Methoden

    async def search_memory_timings(
        self,
        generation: Optional[str] = None,
        vendor: Optional[str] = None,
        ics: Optional[str] = None,
        memclk: Optional[int] = None,
        preset: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryTiming]:
        """
        Durchsuche Memory-Timings-Datenbank mit optionalen Filtern.

        Args:
            generation: CPU-Generation (z.B. zen4, zen3)
            vendor: RAM-Hersteller (z.B. H, C, M)
            ics: Memory-ICs (z.B. 16M, 16A, 24M)
            memclk: Speichertakt in MHz
            preset: Timing-Preset (z.B. lasch, scharf)
            limit: Maximale Anzahl der Ergebnisse

        Returns:
            Liste von MemoryTiming-Objekten
        """
        query = "SELECT * FROM memory_timings WHERE 1=1"
        params = []

        if generation:
            query += " AND generation LIKE ?"
            params.append(f"%{generation}%")

        if vendor:
            query += " AND vendor LIKE ?"
            params.append(f"%{vendor}%")

        if ics:
            query += " AND ics LIKE ?"
            params.append(f"%{ics}%")

        if memclk:
            query += " AND memclk = ?"
            params.append(memclk)

        if preset:
            query += " AND preset LIKE ?"
            params.append(f"%{preset}%")

        query += " ORDER BY memclk DESC, name ASC LIMIT ?"
        params.append(limit)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()

                timings = []
                for row in rows:
                    timing = MemoryTiming(
                        id=row["id"],
                        generation=row["generation"],
                        name=row["name"],
                        rank=row["rank"],
                        vendor=row["vendor"],
                        ics=row["ics"],
                        memclk=row["memclk"],
                        fclk=row["fclk"],
                        preset=row["preset"],
                        pdm=row["pdm"],
                        gdm=row["gdm"],
                        vsoc=row["vsoc"],
                        vdimm=row["vdimm"],
                        vdd=row["vdd"],
                        vddq=row["vddq"],
                        vddio=row["vddio"],
                        vddg=row["vddg"],
                        cldo_vddp=row["cldo_vddp"],
                        vddp=row["vddp"],
                        cads=row["cads"],
                        procodt=row["procodt"],
                        rtts=row["rtts"],
                        tcl=row["tcl"],
                        trcdrp=row["trcdrp"],
                        trcdwr=row["trcdwr"],
                        trcd=row["trcd"],
                        trp=row["trp"],
                        tras=row["tras"],
                        trc=row["trc"],
                        trrds=row["trrds"],
                        trrdl=row["trrdl"],
                        tfaw=row["tfaw"],
                        twtrs=row["twtrs"],
                        twtrl=row["twtrl"],
                        twr=row["twr"],
                        trdrdscl=row["trdrdscl"],
                        twrwrscl=row["twrwrscl"],
                        trefi=row["trefi"],
                        trfc=row["trfc"],
                        tcwl=row["tcwl"],
                        trtp=row["trtp"],
                        trdwr=row["trdwr"],
                        twrrd=row["twrrd"],
                        twrwrsc=row["twrwrsc"],
                        twrwrsd=row["twrwrsd"],
                        twrwrdd=row["twrwrdd"],
                        trdrdsc=row["trdrdsc"],
                        trdrdsd=row["trdrdsd"],
                        trdrddd=row["trdrddd"],
                        tcke=row["tcke"],
                        created_at=row["created_at"],
                    )
                    timings.append(timing)

                return timings

        except Exception as e:
            logger.error(f"Fehler beim Durchsuchen der Memory-Timings: {e}")
            return []

    async def get_memory_timing_filter_options(self) -> dict:
        """
        Hole verfügbare Filter-Optionen für Memory-Timing-Suche.

        Returns:
            Dictionary mit verfügbaren Optionen für verschiedene Filter
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                result = {}

                # Hole verfügbare Generationen
                cursor = await db.execute(
                    "SELECT DISTINCT generation FROM memory_timings ORDER BY generation"
                )
                result["generations"] = [row[0] for row in await cursor.fetchall()]

                # Hole verfügbare Hersteller
                cursor = await db.execute(
                    "SELECT DISTINCT vendor FROM memory_timings WHERE vendor IS NOT NULL ORDER BY vendor"
                )
                result["vendors"] = [row[0] for row in await cursor.fetchall()]

                # Hole verfügbare ICs
                cursor = await db.execute(
                    "SELECT DISTINCT ics FROM memory_timings WHERE ics IS NOT NULL ORDER BY ics"
                )
                result["ics"] = [row[0] for row in await cursor.fetchall()]

                # Hole verfügbare Presets
                cursor = await db.execute(
                    "SELECT DISTINCT preset FROM memory_timings WHERE preset IS NOT NULL ORDER BY preset"
                )
                result["presets"] = [row[0] for row in await cursor.fetchall()]

                # Hole Taktbereich
                cursor = await db.execute(
                    "SELECT MIN(memclk), MAX(memclk) FROM memory_timings WHERE memclk IS NOT NULL"
                )
                clock_range = await cursor.fetchone()
                result["memclk_range"] = clock_range if clock_range else (None, None)

                return result

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Memory-Timing-Filter-Optionen: {e}")
            return {
                "generations": [],
                "vendors": [],
                "ics": [],
                "presets": [],
                "memclk_range": (None, None),
            }
