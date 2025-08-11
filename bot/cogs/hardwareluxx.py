"""
Hardwareluxx News Cog für den Loretta Discord Bot
Überwacht Hardwareluxx RSS-Feed nach Hardware-News
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp
import discord
import feedparser
from discord.ext import commands, tasks

from bot.utils.decorators import track_command_usage
from database import DatabaseManager
from utils.constants import HARDWARE_KEYWORDS

logger = logging.getLogger(__name__)


class Hardwareluxx(commands.Cog):
    """Automatische Überwachung von Hardwareluxx Hardware-News via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None
        self.rss_url = "https://www.hardwareluxx.de/hardwareluxx-newsfeed.feed"
        self.keywords = HARDWARE_KEYWORDS
        self.db_manager = DatabaseManager("database/loretta.db")

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

    def _matches_keywords(self, text: str) -> List[str]:
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
            icon_url="https://github.com/stuoningur/loretta/blob/master/resources/icons/others/hardwareluxx.png?raw=true",
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
            channel_ids = await self.db_manager.get_news_channels()
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
                if await self.db_manager.is_rss_entry_posted(entry_guid):
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
                await self.db_manager.mark_rss_entry_as_posted(
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

    @commands.hybrid_command(
        name="hardwareluxx_info",
        description="Zeigt Informationen über die Hardwareluxx Hardware-News Überwachung",
    )
    @commands.has_permissions(manage_channels=True)
    @track_command_usage
    async def hardwareluxx_info(self, ctx):
        """Zeigt Informationen über die Hardwareluxx Hardware-News Überwachung"""
        try:
            # Aktuellen News-Kanal für diesen Server abrufen
            config = await self.db_manager.get_guild_config(ctx.guild.id)
            news_channel_id = config.news_channel_id

            embed = discord.Embed(
                title="Hardwareluxx Hardware-News Überwachung",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            if news_channel_id:
                news_channel = ctx.guild.get_channel(news_channel_id)
                if news_channel:
                    embed.add_field(
                        name="News-Kanal",
                        value=f"Hardware-News werden in {news_channel.mention} gesendet.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="News-Kanal",
                        value="Konfigurierter Kanal wurde nicht gefunden.",
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="News-Kanal",
                    value="Kein News-Kanal konfiguriert. Verwende `/config news_channel` um einen zu setzen.",
                    inline=False,
                )

            embed.add_field(
                name="Überwachte Hardware-Keywords",
                value=", ".join(self.keywords),
                inline=False,
            )

            embed.add_field(name="RSS-Feed", value=self.rss_url, inline=False)

            embed.add_field(
                name="Überprüfungsintervall", value="Alle 15 Minuten", inline=True
            )

            embed.set_footer(
                text="Hardwareluxx Hardware-News • Automatische Hardware-Nachrichten",
                icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/hardwareluxx.png?raw=true",
            )

            await ctx.send(embed=embed)
            logger.info(
                f"Hardwareluxx-Info angezeigt für Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Hardwareluxx-Informationen: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Fehler beim Abrufen der Hardwareluxx-Informationen.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="hardwareluxx_test",
        description="Testet die Hardwareluxx Hardware-News Funktionalität",
    )
    @commands.has_permissions(manage_channels=True)
    @track_command_usage
    async def test_hardwareluxx_check(self, ctx):
        """Testet den Hardwareluxx RSS-Feed Check manuell"""
        await ctx.defer()

        try:
            if not self.session:
                embed = discord.Embed(
                    title="Fehler",
                    description="HTTP-Session nicht verfügbar.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                await ctx.send(embed=embed)
                return

            # RSS-Feed abrufen
            try:
                async with self.session.get(self.rss_url) as response:
                    if response.status != 200:
                        embed = discord.Embed(
                            title="RSS-Feed Fehler",
                            description=f"HTTP Status: {response.status}",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc),
                        )
                        await ctx.send(embed=embed)
                        return

                    content = await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                embed = discord.Embed(
                    title="RSS-Feed Verbindungsfehler",
                    description="Verbindung fehlgeschlagen",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                await ctx.send(embed=embed)
                return
            except Exception as e:
                embed = discord.Embed(
                    title="RSS-Feed Fehler",
                    description=f"Unerwarteter Fehler: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                await ctx.send(embed=embed)
                return

            # RSS-Feed parsen
            try:
                feed = feedparser.parse(content)
                if not hasattr(feed, "entries"):
                    embed = discord.Embed(
                        title="RSS-Feed Parser-Fehler",
                        description="RSS-Feed hat ungültiges Format",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc),
                    )
                    await ctx.send(embed=embed)
                    return
            except Exception as e:
                embed = discord.Embed(
                    title="RSS-Feed Parser-Fehler",
                    description=f"Parser-Fehler: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                await ctx.send(embed=embed)
                return

            if not feed.entries:
                embed = discord.Embed(
                    title="RSS-Feed Test",
                    description="Keine Einträge im Hardwareluxx RSS-Feed gefunden.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc),
                )
                await ctx.send(embed=embed)
                return

            # Statistiken sammeln
            total_entries = len(feed.entries)
            keyword_matches = 0
            matched_entries = []

            for entry in feed.entries:
                search_text = str(entry.title)
                if hasattr(entry, "tags") and entry.tags:
                    search_text += " " + str(entry.tags[0].get("term", ""))

                matched_keywords = self._matches_keywords(search_text)
                if matched_keywords:
                    keyword_matches += 1
                    matched_entries.append((str(entry.title), matched_keywords))

            # Test-Ergebnis anzeigen
            embed = discord.Embed(
                title="Hardwareluxx Hardware-News Test",
                description="RSS-Feed erfolgreich getestet",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.add_field(
                name="Feed-Statistiken",
                value=f"**Gesamte Einträge:** {total_entries}\n**Hardware-Keyword-Treffer:** {keyword_matches}",
                inline=False,
            )

            embed.add_field(name="RSS-Feed URL", value=self.rss_url, inline=False)

            embed.add_field(
                name="Überwachte Hardware-Keywords",
                value=", ".join(self.keywords),
                inline=False,
            )

            # Aktuelle News-Kanäle anzeigen
            news_channels = await self.db_manager.get_news_channels()
            if news_channels:
                embed.add_field(
                    name="Aktive News-Kanäle",
                    value=f"{len(news_channels)} Kanal(e) konfiguriert",
                    inline=True,
                )
            else:
                embed.add_field(
                    name="Aktive News-Kanäle",
                    value="Keine News-Kanäle konfiguriert",
                    inline=True,
                )

            # Zeige die ersten 3 Hardware-Treffer
            if matched_entries:
                matches_text = ""
                for i, (title, keywords) in enumerate(matched_entries[:3]):
                    matches_text += f"**{i + 1}.** {title}\n*Hardware-Keywords: {', '.join(keywords)}*\n\n"

                if len(matched_entries) > 3:
                    matches_text += f"... und {len(matched_entries) - 3} weitere"

                embed.add_field(
                    name="Aktuelle Hardware-Treffer (Beispiele)",
                    value=matches_text,
                    inline=False,
                )

            embed.set_footer(
                text="Hardwareluxx Hardware-News • Test-Ergebnis",
                icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/hardwareluxx.png?raw=true",
            )

            await ctx.send(embed=embed)
            logger.info(
                f"Hardwareluxx Hardware-News Test ausgeführt von {ctx.author} in Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Hardwareluxx Hardware-News Test: {e}")
            embed = discord.Embed(
                title="Test Fehler",
                description=f"Fehler beim Testen der Hardwareluxx Hardware-News Funktionalität: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Hardwareluxx Hardware-News Cog"""
    await bot.add_cog(Hardwareluxx(bot))
    logger.info("Hardwareluxx News Cog geladen und RSS-Überwachung gestartet")
