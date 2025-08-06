"""
PCGH News Cog für den Loretta Discord Bot
Überwacht PC Games Hardware RSS-Feeds nach Hardware-News
"""

import discord
from discord.ext import commands, tasks
import aiohttp
import feedparser
import logging
from datetime import datetime, timezone
from typing import Optional, List
import asyncio
from utils.database import DatabaseManager
from utils.constants import HARDWARE_KEYWORDS

logger = logging.getLogger(__name__)


class PCGH(commands.Cog):
    """Automatische Überwachung von PC Games Hardware News via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None
        self.rss_urls = [
            "https://www.pcgameshardware.de/feed.cfm?menu_alias=Test/",
            "https://www.pcgameshardware.de/feed.cfm",
        ]
        self.keywords = HARDWARE_KEYWORDS
        self.db_manager = DatabaseManager("data/loretta.db")

    async def cog_load(self):
        """Initialisiert die HTTP-Session und startet den RSS-Check"""
        self.session = aiohttp.ClientSession()
        self.check_rss_feed.start()
        logger.info("PCGH News Cog geladen und RSS-Überwachung gestartet")

    async def cog_unload(self):
        """Stoppt die RSS-Überwachung und schließt die HTTP-Session"""
        self.check_rss_feed.cancel()
        if self.session:
            await self.session.close()
        logger.info("PCGH News Cog entladen und RSS-Überwachung gestoppt")

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

    def _extract_image_url(self, html_content: str) -> Optional[str]:
        """Extrahiert die erste Bild-URL aus HTML-Content"""
        if not html_content:
            return None

        import re

        # Suche nach <img src="..."> Tags
        img_match = re.search(
            r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_content, re.IGNORECASE
        )
        if img_match:
            return img_match.group(1)
        return None

    async def _create_news_embed(self, entry) -> discord.Embed:
        """Erstellt ein Embed für eine Hardware-News"""
        embed = discord.Embed(
            title=entry.title,
            url=entry.link,
            color=discord.Color.dark_blue(),
            timestamp=datetime.now(timezone.utc),
        )

        # Thumbnail-Bild aus RSS-Feed extrahieren
        image_url = None
        
        # Zuerst prüfen, ob ein Enclosure-Tag mit einem Bild vorhanden ist
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enclosure in entry.enclosures:
                if hasattr(enclosure, "type") and enclosure.type and enclosure.type.startswith("image/"):
                    if hasattr(enclosure, "url") and enclosure.url:
                        image_url = enclosure.url
                        break
        
        # Falls kein Enclosure-Bild gefunden wurde, aus HTML-Summary extrahieren
        if not image_url and hasattr(entry, "summary") and entry.summary:
            image_url = self._extract_image_url(entry.summary)
        
        if image_url:
            embed.set_thumbnail(url=image_url)

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

        # PCGH Footer hinzufügen
        embed.set_footer(
            text="PC Games Hardware • Nachrichten",
            icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/pcgh.png?raw=true",
        )

        return embed


    @tasks.loop(minutes=15)
    async def check_rss_feed(self):
        """Überprüft die RSS-Feeds alle 15 Minuten"""
        try:
            if not self.session:
                logger.warning("HTTP-Session nicht verfügbar für PCGH RSS-Check")
                return

            # News-Kanäle abrufen
            channel_ids = await self.db_manager.get_news_channels()
            if not channel_ids:
                logger.debug("Keine News-Kanäle für PCGH-News konfiguriert")
                return

            # Alle Feeds abrufen und kombinieren
            all_entries = []
            
            for i, rss_url in enumerate(self.rss_urls):
                feed_type = "test" if i == 0 else "main"
                
                try:
                    # RSS-Feed abrufen
                    async with self.session.get(rss_url) as response:
                        if response.status != 200:
                            logger.error(
                                f"PCGH RSS-Feed Fehler ({feed_type}): HTTP {response.status} für {rss_url}"
                            )
                            continue

                        content = await response.text()

                    # RSS-Feed parsen
                    feed = feedparser.parse(content)

                    if not feed.entries:
                        logger.warning(
                            f"Keine Einträge im PCGH RSS-Feed ({feed_type}) gefunden: {rss_url}"
                        )
                        continue

                    # Entries mit Feed-Typ markieren und zur Liste hinzufügen  
                    for idx, entry in enumerate(feed.entries):
                        # Einfache Sortierung basierend auf Feed-Reihenfolge
                        # RSS-Feeds sind normalerweise bereits chronologisch sortiert
                        sort_key = idx
                        
                        # Entry mit zusätzlichen Metadaten als Tuple erweitern
                        all_entries.append((entry, feed_type, sort_key))

                except Exception as e:
                    logger.error(f"Fehler beim Abrufen des PCGH RSS-Feeds ({feed_type}): {e}")
                    continue

            if not all_entries:
                logger.debug("Keine Einträge in beiden PCGH RSS-Feeds gefunden")
                return

            # Entries nach Index sortieren (älteste zuerst, neueste zuletzt)
            all_entries.sort(key=lambda x: x[2], reverse=True)  # x[2] ist sort_key

            # Alle Entries verarbeiten
            new_entries_count = 0
            for entry, feed_type, sort_key in all_entries:
                # GUID für Eindeutigkeit verwenden, ohne Feed-Typ um Duplikate zu vermeiden
                entry_guid = f"pcgh_{str(getattr(entry, 'id', entry.link))}"
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
                                f"PCGH Hardware-News ({feed_type}) gesendet an News-Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {entry.title}"
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
                                f"Fehler beim Senden von PCGH-News ({feed_type}) an Kanal '{channel.name}' in Guild '{guild_name}' ({channel_id}): {e}"
                            )
                        else:
                            logger.error(
                                f"Fehler beim Senden von PCGH-News ({feed_type}) an Kanal {channel_id}: {e}"
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
                    f"{new_entries_count} neue PCGH Hardware-News an {len(channel_ids)} News-Kanäle gesendet: {', '.join(channel_info)}"
                )

        except Exception as e:
            logger.error(f"Fehler beim PCGH RSS-Feed Check: {e}")

    @check_rss_feed.before_loop
    async def before_rss_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()

    @commands.hybrid_command(
        name="pcgh_info",
        description="Zeigt Informationen über die PCGH Hardware-News Überwachung",
    )
    @commands.has_permissions(manage_channels=True)
    async def pcgh_info(self, ctx):
        """Zeigt Informationen über die PCGH Hardware-News Überwachung"""
        try:
            # Aktuellen News-Kanal für diesen Server abrufen
            config = await self.db_manager.get_server_config(ctx.guild.id)
            news_channel_id = config.news_channel_id

            embed = discord.Embed(
                title="PCGH Hardware-News Überwachung",
                color=discord.Color.dark_blue(),
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

            embed.add_field(
                name="RSS-Feeds",
                value="\n".join([f"• {url}" for url in self.rss_urls]),
                inline=False,
            )

            embed.add_field(
                name="Überprüfungsintervall", value="Alle 15 Minuten", inline=True
            )

            embed.set_footer(
                text="PC Games Hardware • Automatische Hardware-Nachrichten",
                icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/pcgh.png?raw=true",
            )

            await ctx.send(embed=embed)
            logger.info(
                f"PCGH-Info angezeigt für Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der PCGH-Informationen: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Fehler beim Abrufen der PCGH-Informationen.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="pcgh_test",
        description="Testet die PCGH Hardware-News Funktionalität",
    )
    @commands.has_permissions(manage_channels=True)
    async def test_pcgh_check(self, ctx):
        """Testet die PCGH RSS-Feed Checks manuell"""
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

            total_entries = 0
            total_keyword_matches = 0
            feed_results = []

            # Beide Feeds testen
            for i, rss_url in enumerate(self.rss_urls):
                feed_name = "Test-Feed" if i == 0 else "Haupt-Feed"

                try:
                    # RSS-Feed abrufen
                    async with self.session.get(rss_url) as response:
                        if response.status != 200:
                            feed_results.append(
                                f"**{feed_name}**: HTTP {response.status} Fehler"
                            )
                            continue

                        content = await response.text()

                    # RSS-Feed parsen
                    feed = feedparser.parse(content)

                    if not feed.entries:
                        feed_results.append(f"**{feed_name}**: Keine Einträge gefunden")
                        continue

                    # Statistiken sammeln
                    feed_entries = len(feed.entries)
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

                    total_entries += feed_entries
                    total_keyword_matches += keyword_matches
                    feed_results.append(
                        f"**{feed_name}**: {feed_entries} Einträge, {keyword_matches} Treffer"
                    )

                except Exception as e:
                    feed_results.append(f"**{feed_name}**: Fehler - {str(e)}")

            # Test-Ergebnis anzeigen
            embed = discord.Embed(
                title="PCGH Hardware-News Test",
                description="RSS-Feeds erfolgreich getestet",
                color=discord.Color.dark_blue(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.add_field(
                name="Gesamt-Statistiken",
                value=f"**Gesamte Einträge:** {total_entries}\n**Hardware-Keyword-Treffer:** {total_keyword_matches}",
                inline=False,
            )

            embed.add_field(
                name="Feed-Details",
                value="\n".join(feed_results),
                inline=False,
            )

            embed.add_field(
                name="RSS-Feed URLs",
                value="\n".join([f"• {url}" for url in self.rss_urls]),
                inline=False,
            )

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

            embed.set_footer(
                text="PC Games Hardware • Test-Ergebnis",
                icon_url="https://github.com/stuoningur/loretta/blob/master/data/icons/others/pcgh.png?raw=true",
            )

            await ctx.send(embed=embed)
            logger.info(
                f"PCGH Hardware-News Test ausgeführt von {ctx.author} in Guild '{ctx.guild.name}' ({ctx.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim PCGH Hardware-News Test: {e}")
            embed = discord.Embed(
                title="Test Fehler",
                description=f"Fehler beim Testen der PCGH Hardware-News Funktionalität: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das PCGH Hardware-News Cog"""
    await bot.add_cog(PCGH(bot))
    logger.info("PCGH Hardware-News Cog geladen")
