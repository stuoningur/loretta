"""
Software Check Cog für den Loretta Discord Bot
Überwacht RSS-Feeds nach Software-Downloads
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, List

import discord
import aiohttp
import feedparser
from discord.ext import commands, tasks

from utils.database import DatabaseManager
from utils.decorators import track_command_usage

logger = logging.getLogger(__name__)


class SoftwareCheck(commands.Cog):
    """Automatische Überwachung von Software-Downloads via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None
        self.rss_url = "https://www.computerbase.de/rss/downloads.xml"
        self.keywords = [
            "aida64",
            "hwinfo",
            "cpu-z",
            "gpu-z",
            "zentimings",
            "amd",
            "nvidia",
            "intel",
        ]
        self.db_manager = DatabaseManager("data/loretta.db")

    async def cog_load(self):
        """Initialisiert die HTTP-Session und startet den RSS-Check"""
        self.session = aiohttp.ClientSession()
        self.check_rss_feed.start()

    async def cog_unload(self):
        """Stoppt die RSS-Überwachung und schließt die HTTP-Session"""
        self.check_rss_feed.cancel()
        if self.session:
            await self.session.close()
        logger.info("Software Check Cog entladen und RSS-Überwachung gestoppt")

    def _matches_keywords(self, text: str) -> List[str]:
        """Prüft, ob der Text eines der Keywords enthält"""
        text_lower = text.lower()
        matched_keywords = []

        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)

        return matched_keywords

    async def _create_software_embed(self, entry) -> discord.Embed:
        """Erstellt ein Embed für eine Software-Update"""
        embed = discord.Embed(
            title=entry.title,
            url=entry.link,
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Beschreibung hinzufügen falls vorhanden
        if hasattr(entry, "summary") and entry.summary:
            # HTML-Tags entfernen und Text kürzen
            import re

            clean_summary = re.sub(r"<[^>]+>", "", entry.summary)
            if len(clean_summary) > 200:
                clean_summary = clean_summary[:200] + "..."
            embed.add_field(name="Beschreibung", value=clean_summary, inline=False)

        # Veröffentlichungsdatum falls vorhanden
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            embed.add_field(
                name="Veröffentlicht",
                value=f"<t:{int(pub_date.timestamp())}:R>",
                inline=True,
            )

        # ComputerBase favicon im Footer hinzufügen
        embed.set_footer(
            text="ComputerBase Downloads • Automatische Benachrichtigung",
            icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/computerbase.png?raw=true",
        )

        return embed

    @tasks.loop(minutes=15)
    async def check_rss_feed(self):
        """Überprüft den RSS-Feed alle 15 Minuten"""
        try:
            if not self.session:
                logger.warning("HTTP-Session nicht verfügbar für RSS-Check")
                return

            # RSS-Feed abrufen
            async with self.session.get(self.rss_url) as response:
                if response.status != 200:
                    logger.error(f"RSS-Feed Fehler: HTTP {response.status}")
                    return

                content = await response.text()

            # RSS-Feed parsen
            feed = feedparser.parse(content)

            if not feed.entries:
                logger.warning("Keine Einträge im RSS-Feed gefunden")
                return

            # News-Kanäle abrufen
            channel_ids = await self.db_manager.get_news_channels()
            if not channel_ids:
                logger.debug("Keine News-Kanäle konfiguriert")
                return

            # Neue Einträge verarbeiten (älteste zuerst, damit neueste zuletzt gepostet werden)
            new_entries_count = 0
            for entry in reversed(feed.entries):
                # GUID für Eindeutigkeit verwenden
                entry_guid = str(getattr(entry, "id", entry.link))
                entry_title = str(entry.title)
                entry_link = str(entry.link)

                # Prüfen, ob bereits gepostet
                if await self.db_manager.is_rss_entry_posted(entry_guid):
                    continue

                # Keywords im Titel und Beschreibung prüfen
                search_text = entry_title
                if hasattr(entry, "summary") and entry.summary:
                    search_text += " " + str(entry.summary)

                matched_keywords = self._matches_keywords(search_text)
                if not matched_keywords:
                    # Überspringen ohne zu speichern - nur relevante Einträge werden gespeichert
                    continue

                # Embed erstellen
                embed = await self._create_software_embed(entry)

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
                                f"Software-Update gesendet an News-Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {entry.title}"
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
                                f"Fehler beim Senden an Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {e}"
                            )
                        else:
                            logger.error(
                                f"Fehler beim Senden an Kanal {channel_id}: {e}"
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
                    f"{new_entries_count} neue Software-Updates an {len(channel_ids)} News-Kanäle gesendet: {', '.join(channel_info)}"
                )

        except Exception as e:
            logger.error(f"Fehler beim RSS-Feed Check: {e}")

    @check_rss_feed.before_loop
    async def before_rss_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()

    @commands.hybrid_command(
        name="software_info",
        description="Zeigt Informationen über die Software-Überwachung",
    )
    @commands.has_permissions(manage_channels=True)
    @track_command_usage
    async def software_info(self, ctx):
        """Zeigt Informationen über die Software-Überwachung"""
        try:
            # Aktuellen News-Kanal für diesen Server abrufen
            config = await self.db_manager.get_guild_config(ctx.guild.id)
            news_channel_id = config.news_channel_id

            embed = discord.Embed(
                title="Software-Überwachung Informationen",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )

            if news_channel_id:
                news_channel = ctx.guild.get_channel(news_channel_id)
                if news_channel:
                    embed.add_field(
                        name="News-Kanal",
                        value=f"Software-Updates werden in {news_channel.mention} gesendet.",
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
                name="Überwachte Keywords", value=", ".join(self.keywords), inline=False
            )

            embed.add_field(name="RSS-Feed", value=self.rss_url, inline=False)

            embed.add_field(
                name="Überprüfungsintervall", value="Alle 15 Minuten", inline=True
            )

            await ctx.send(embed=embed)
            logger.info(
                f"Software-Info angezeigt für Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Software-Informationen: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Fehler beim Abrufen der Software-Informationen.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="software_test", description="Testet die Software-Check Funktionalität"
    )
    @commands.has_permissions(manage_channels=True)
    @track_command_usage
    async def test_software_check(self, ctx):
        """Testet den RSS-Feed Check manuell"""
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

            # RSS-Feed parsen
            feed = feedparser.parse(content)

            if not feed.entries:
                embed = discord.Embed(
                    title="RSS-Feed Test",
                    description="Keine Einträge im RSS-Feed gefunden.",
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
                if hasattr(entry, "summary") and entry.summary:
                    search_text += " " + str(entry.summary)

                matched_keywords = self._matches_keywords(search_text)
                if matched_keywords:
                    keyword_matches += 1
                    matched_entries.append((str(entry.title), matched_keywords))

            # Test-Ergebnis anzeigen
            embed = discord.Embed(
                title="Software-Check Test",
                description="RSS-Feed erfolgreich getestet",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.add_field(
                name="Feed-Statistiken",
                value=f"**Gesamte Einträge:** {total_entries}\n**Keyword-Treffer:** {keyword_matches}",
                inline=False,
            )

            embed.add_field(name="RSS-Feed URL", value=self.rss_url, inline=False)

            embed.add_field(
                name="Überwachte Keywords", value=", ".join(self.keywords), inline=False
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

            # Zeige die ersten 3 Treffer
            if matched_entries:
                matches_text = ""
                for i, (title, keywords) in enumerate(matched_entries[:3]):
                    matches_text += (
                        f"**{i + 1}.** {title}\n*Keywords: {', '.join(keywords)}*\n\n"
                    )

                if len(matched_entries) > 3:
                    matches_text += f"... und {len(matched_entries) - 3} weitere"

                embed.add_field(
                    name="Aktuelle Treffer (Beispiele)",
                    value=matches_text,
                    inline=False,
                )

            await ctx.send(embed=embed)
            logger.info(
                f"Software-Check Test ausgeführt von {ctx.author} in Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Software-Check Test: {e}")
            embed = discord.Embed(
                title="Test Fehler",
                description=f"Fehler beim Testen der Software-Check Funktionalität: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Software Check Cog"""
    await bot.add_cog(SoftwareCheck(bot))
    logger.info("Software Check Cog geladen und RSS-Überwachung gestartet")
