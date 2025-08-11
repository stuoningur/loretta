"""
Hardwareluxx News Cog für den Loretta Discord Bot
Überwacht Hardwareluxx RSS-Feed nach Hardware-News
"""

import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
import discord
import feedparser
from discord.ext import commands, tasks

from utils.constants import HARDWARE_KEYWORDS

logger = logging.getLogger(__name__)


class Hardwareluxx(commands.Cog):
    """Automatische Überwachung von Hardwareluxx Hardware-News via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.rss_url = "https://www.hardwareluxx.de/hardwareluxx-newsfeed.feed"
        self.keywords = HARDWARE_KEYWORDS

    async def cog_load(self):
        """Initialisiert die HTTP-Session und startet den RSS-Check"""
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        self.session = aiohttp.ClientSession(timeout=timeout)
        self.check_rss_feed.start()

    async def cog_unload(self):
        """Stoppt die RSS-Überwachung und schließt die HTTP-Session"""
        self.check_rss_feed.cancel()
        if self.session:
            await self.session.close()
        logger.info("Hardwareluxx News Cog entladen und RSS-Überwachung gestoppt")

    def _matches_keywords(self, text: str) -> list[str]:
        """Prüft, ob der Text eines der Keywords als ganze Wörter enthält"""
        import re

        text_lower = text.lower()
        matched_keywords = []

        for keyword in self.keywords:
            # Verwende Wortgrenzen (\b) für exakte Wort-Übereinstimmung
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, text_lower):
                matched_keywords.append(keyword)

        return matched_keywords

    async def _create_news_embed(self, entry) -> discord.Embed:
        """Erstellt ein Embed für eine Hardware-News"""
        embed = discord.Embed(
            title=entry.title,
            url=entry.link,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )

        # Kategorie hinzufügen falls vorhanden
        if hasattr(entry, "tags") and entry.tags:
            category = entry.tags[0].get("term", "")
            if category:
                embed.add_field(name="Kategorie", value=category, inline=True)

        # Veröffentlichungsdatum falls vorhanden
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            embed.add_field(
                name="Veröffentlicht",
                value=f"<t:{int(pub_date.timestamp())}:R>",
                inline=True,
            )

        # Hardwareluxx Footer hinzufügen
        embed.set_footer(
            text="Hardwareluxx • Nachrichten",
            icon_url="https://github.com/stuoningur/loretta/blob/master/resources/icons/rss/hardwareluxx.png?raw=true",
        )

        return embed

    @tasks.loop(minutes=15)
    async def check_rss_feed(self):
        """Überprüft den RSS-Feed alle 15 Minuten"""
        try:
            if not self.session:
                logger.warning(
                    "HTTP-Session nicht verfügbar für Hardwareluxx RSS-Check"
                )
                return

            # RSS-Feed abrufen
            try:
                async with self.session.get(self.rss_url) as response:
                    if response.status != 200:
                        logger.error(
                            f"Hardwareluxx RSS-Feed Fehler: HTTP {response.status}"
                        )
                        return

                    content = await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                logger.error("Hardwareluxx RSS-Feed Verbindungsfehler")
                return
            except Exception as e:
                logger.error(f"Hardwareluxx RSS-Feed unerwarteter Fehler: {e}")
                return

            # RSS-Feed parsen
            try:
                feed = feedparser.parse(content)
                if not hasattr(feed, "entries"):
                    logger.error("Hardwareluxx RSS-Feed hat ungültiges Format")
                    return
            except Exception as e:
                logger.error(f"Hardwareluxx RSS-Feed Parser-Fehler: {e}")
                return

            if not feed.entries:
                logger.warning("Keine Einträge im Hardwareluxx RSS-Feed gefunden")
                return

            # News-Kanäle abrufen
            channel_ids = await self.bot.db.get_news_channels()
            if not channel_ids:
                logger.debug("Keine News-Kanäle für Hardwareluxx-News konfiguriert")
                return

            # Neue Einträge verarbeiten (älteste zuerst, damit neueste zuletzt gepostet werden)
            new_entries_count = 0
            for entry in reversed(feed.entries):
                # GUID für Eindeutigkeit verwenden, mit Präfix für Hardwareluxx
                entry_guid = f"hlx_news_{str(getattr(entry, 'id', entry.link))}"
                entry_title = str(entry.title)
                entry_link = str(entry.link)

                # Prüfen, ob bereits gepostet
                if await self.bot.db.is_rss_entry_posted(entry_guid):
                    continue

                # Keywords im Titel und Kategorie prüfen
                search_text = entry_title
                if hasattr(entry, "tags") and entry.tags:
                    search_text += " " + str(entry.tags[0].get("term", ""))

                matched_keywords = self._matches_keywords(search_text)
                if not matched_keywords:
                    # Überspringen ohne zu speichern - nur relevante Einträge werden gespeichert
                    continue

                # Embed erstellen
                embed = await self._create_news_embed(entry)

                # An alle konfigurierten Kanäle senden
                for channel_id in channel_ids:
                    try:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(embed=embed)
                            guild_name = (
                                channel.guild.name if channel.guild else "Unknown Guild"
                            )
                            logger.info(
                                f"Hardwareluxx Hardware-News gesendet an News-Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {entry.title}"
                            )
                        else:
                            logger.warning(f"Kanal {channel_id} nicht gefunden")
                    except Exception as e:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            guild_name = (
                                channel.guild.name if channel.guild else "Unknown Guild"
                            )
                            logger.error(
                                f"Fehler beim Senden von Hardwareluxx-News an Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {e}"
                            )
                        else:
                            logger.error(
                                f"Fehler beim Senden von Hardwareluxx-News an Kanal {channel_id}: {e}"
                            )

                # Als gepostet markieren
                await self.bot.db.mark_rss_entry_as_posted(
                    entry_guid, entry_title, entry_link
                )
                new_entries_count += 1

                # Kleine Pause zwischen den Posts
                await asyncio.sleep(1)

            if new_entries_count > 0:
                # Sammle Kanalinformationen für besseres Logging
                channel_info = []
                for channel_id in channel_ids:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        guild_name = (
                            channel.guild.name if channel.guild else "Unknown Guild"
                        )
                        channel_info.append(f"#{channel.name} ({guild_name})")
                    else:
                        channel_info.append(f"ID:{channel_id} (nicht gefunden)")

                logger.info(
                    f"{new_entries_count} neue Hardwareluxx Hardware-News an {len(channel_ids)} News-Kanäle gesendet: {', '.join(channel_info)}"
                )

        except Exception as e:
            logger.error(f"Fehler beim Hardwareluxx RSS-Feed Check: {e}")

    @check_rss_feed.before_loop
    async def before_rss_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Lädt das Hardwareluxx Hardware-News Cog"""
    await bot.add_cog(Hardwareluxx(bot))
    logger.info("Hardwareluxx News Cog geladen und RSS-Überwachung gestartet")
