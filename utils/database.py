"""
Datenbank-Utility-Funktionen für Server-Konfigurationsverwaltung.
"""

import aiosqlite
import json
import logging
from typing import Optional, List, Tuple, Union
from dataclasses import dataclass, field
from datetime import date
import discord

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Datenklasse für Server-Konfiguration."""

    guild_id: int
    command_prefix: str = "!"
    log_channel_id: Optional[int] = None
    news_channel_id: Optional[int] = None
    picture_only_channels: List[int] = field(default_factory=list)


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


class DatabaseManager:
    """Manager-Klasse für Datenbankoperationen."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get_server_config(self, guild_id: int) -> ServerConfig:
        """
        Holt die Server-Konfiguration für eine Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            ServerConfig-Objekt mit der Guild-Konfiguration
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, news_channel_id, picture_only_channels "
                    "FROM server_config WHERE guild_id = ?",
                    (guild_id,),
                )
                row = await cursor.fetchone()

                if row:
                    picture_only_channels = json.loads(row[4]) if row[4] else []
                    return ServerConfig(
                        guild_id=row[0],
                        command_prefix=row[1],
                        log_channel_id=row[2],
                        news_channel_id=row[3],
                        picture_only_channels=picture_only_channels,
                    )
                else:
                    # Gib Standard-Konfiguration für neue Guilds zurück
                    return ServerConfig(guild_id=guild_id)

        except Exception as e:
            logger.error(
                f"Fehler beim Abrufen der Server-Konfiguration für Guild {guild_id}: {e}"
            )
            # Gib Standard-Konfiguration bei Fehler zurück
            return ServerConfig(guild_id=guild_id)

    async def set_server_config(self, config: ServerConfig) -> bool:
        """
        Setzt die Server-Konfiguration für eine Guild.

        Args:
            config: ServerConfig-Objekt mit der neuen Konfiguration

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            picture_only_json = json.dumps(config.picture_only_channels)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO server_config 
                       (guild_id, command_prefix, log_channel_id, news_channel_id, picture_only_channels)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        config.guild_id,
                        config.command_prefix,
                        config.log_channel_id,
                        config.news_channel_id,
                        picture_only_json,
                    ),
                )
                await db.commit()

            logger.info(
                f"Server-Konfiguration für Guild {config.guild_id} aktualisiert"
            )
            return True

        except Exception as e:
            logger.error(
                f"Fehler beim Setzen der Server-Konfiguration für Guild {config.guild_id}: {e}"
            )
            return False

    async def set_command_prefix(self, guild_id: int, prefix: str) -> bool:
        """
        Setzt das Command-Prefix für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            prefix: Neues Command-Prefix

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_server_config(guild_id)
            config.command_prefix = prefix
            return await self.set_server_config(config)

        except Exception as e:
            logger.error(
                f"Fehler beim Setzen des Command-Prefix für Guild {guild_id}: {e}"
            )
            return False

    async def set_log_channel(self, guild_id: int, channel_id: Optional[int]) -> bool:
        """
        Setzt den Log-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID für Logging, None zum Deaktivieren

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_server_config(guild_id)
            config.log_channel_id = channel_id
            return await self.set_server_config(config)

        except Exception as e:
            logger.error(f"Fehler beim Setzen des Log-Kanals für Guild {guild_id}: {e}")
            return False

    async def set_news_channel(self, guild_id: int, channel_id: Optional[int]) -> bool:
        """
        Setzt den News-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID für News, None zum Deaktivieren

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_server_config(guild_id)
            config.news_channel_id = channel_id
            return await self.set_server_config(config)

        except Exception as e:
            logger.error(
                f"Fehler beim Setzen des News-Kanals für Guild {guild_id}: {e}"
            )
            return False

    async def add_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Fügt einen Kanal zur Liste der Nur-Bild-Kanäle hinzu.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID zum Hinzufügen

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_server_config(guild_id)
            if channel_id not in config.picture_only_channels:
                config.picture_only_channels.append(channel_id)
                return await self.set_server_config(config)
            return True

        except Exception as e:
            logger.error(
                f"Fehler beim Hinzufügen des Nur-Bild-Kanals für Guild {guild_id}: {e}"
            )
            return False

    async def remove_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Entfernt einen Kanal aus der Liste der Nur-Bild-Kanäle.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Kanal-ID zum Entfernen

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            config = await self.get_server_config(guild_id)
            if channel_id in config.picture_only_channels:
                config.picture_only_channels.remove(channel_id)
                return await self.set_server_config(config)
            return True

        except Exception as e:
            logger.error(
                f"Fehler beim Entfernen des Nur-Bild-Kanals für Guild {guild_id}: {e}"
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
            config = await self.get_server_config(guild_id)
            return channel_id in config.picture_only_channels

        except Exception as e:
            logger.error(
                f"Fehler beim Überprüfen des Nur-Bild-Kanals für Guild {guild_id}: {e}"
            )
            return False

    async def get_all_server_configs(self) -> List[ServerConfig]:
        """
        Holt alle Server-Konfigurationen.

        Returns:
            Liste von ServerConfig-Objekten
        """
        try:
            configs = []
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, news_channel_id, picture_only_channels "
                    "FROM server_config"
                )
                rows = await cursor.fetchall()

                for row in rows:
                    picture_only_channels = json.loads(row[4]) if row[4] else []
                    configs.append(
                        ServerConfig(
                            guild_id=row[0],
                            command_prefix=row[1],
                            log_channel_id=row[2],
                            news_channel_id=row[3],
                            picture_only_channels=picture_only_channels,
                        )
                    )

            return configs

        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Server-Konfigurationen: {e}")
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
                    "SELECT news_channel_id FROM server_config WHERE news_channel_id IS NOT NULL"
                )
                results = await cursor.fetchall()
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der News-Kanäle: {e}")
            return []

    # Geburtstags-Verwaltungs-Methoden

    async def add_birthday(self, birthday: Birthday) -> bool:
        """
        Fügt einen Benutzer-Geburtstag hinzu oder aktualisiert ihn.

        Args:
            birthday: Birthday-Objekt mit Benutzer-Geburtstagsinformationen

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

            logger.info(
                f"Geburtstag für Benutzer {birthday.user_id} in Guild {birthday.guild_id} hinzugefügt"
            )
            return True

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Geburtstags: {e}")
            return False

    async def remove_birthday(self, guild_id: int, user_id: int) -> bool:
        """
        Entfernt einen Benutzer-Geburtstag.

        Args:
            guild_id: Discord Guild-ID
            user_id: Discord Benutzer-ID

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

            logger.info(
                f"Geburtstag für Benutzer {user_id} in Guild {guild_id} entfernt"
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

    async def add_birthday_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Fügt einen Geburtstags-Ankündigungs-Kanal für eine Guild hinzu.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Discord Kanal-ID

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO birthday_channels (guild_id, channel_id) VALUES (?, ?)",
                    (guild_id, channel_id),
                )
                await db.commit()

            logger.info(
                f"Geburtstags-Kanal {channel_id} für Guild {guild_id} hinzugefügt"
            )
            return True

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Geburtstags-Kanals: {e}")
            return False

    async def remove_birthday_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Entfernt einen Geburtstags-Ankündigungs-Kanal für eine Guild.

        Args:
            guild_id: Discord Guild-ID
            channel_id: Discord Kanal-ID

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM birthday_channels WHERE guild_id = ? AND channel_id = ?",
                    (guild_id, channel_id),
                )
                await db.commit()

            logger.info(f"Geburtstags-Kanal {channel_id} für Guild {guild_id} entfernt")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Geburtstags-Kanals: {e}")
            return False

    async def get_birthday_channels(self, guild_id: int) -> List[int]:
        """
        Holt alle Geburtstags-Ankündigungs-Kanäle für eine Guild.

        Args:
            guild_id: Discord Guild-ID

        Returns:
            Liste von Kanal-IDs
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT channel_id FROM birthday_channels WHERE guild_id = ?",
                    (guild_id,),
                )
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Geburtstags-Kanäle: {e}")
            return []

    async def get_all_birthday_channels(self) -> List[Tuple[int, int]]:
        """
        Holt alle Geburtstags-Ankündigungs-Kanäle über alle Guilds hinweg.

        Returns:
            Liste von Tupeln (guild_id, channel_id)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, channel_id FROM birthday_channels"
                )
                rows = await cursor.fetchall()
                return [(row[0], row[1]) for row in rows]

        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Geburtstags-Kanäle: {e}")
            return []

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
