"""
Hardwareluxx News Cog für den Loretta Discord Bot
Überwacht Hardwareluxx RSS-Feed nach Hardware-News
"""

import logging

import aiohttp
import discord
from discord.ext import commands, tasks

from bot.utils.embeds import EmbedFactory
from bot.utils.rss_feed import process_rss_feed
from utils.constants import HARDWARE_KEYWORDS

logger = logging.getLogger(__name__)


class Hardwareluxx(commands.Cog):
    """Automatische Überwachung von Hardwareluxx Hardware-News via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.rss_urls = ["https://www.hardwareluxx.de/hardwareluxx-newsfeed.feed"]
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

    async def _create_news_embed(self, entry) -> discord.Embed:
        """Erstellt ein Embed für eine Hardware-News"""
        return EmbedFactory.rss_news_embed(
            entry=entry,
            source="hardwareluxx",
            include_description=False,
            include_thumbnail=False,
            include_category=True,
        )

    def _extract_search_text(self, entry):
        """
        Extrahiert den Suchtext für Hardwareluxx (Titel + Tags)
        """
        search_text = str(entry.title)
        if hasattr(entry, "tags") and entry.tags:
            search_text += " " + str(entry.tags[0].get("term", ""))
        return search_text

    @tasks.loop(minutes=15)
    async def check_rss_feed(self):
        """Überprüft den RSS-Feed alle 15 Minuten"""
        await process_rss_feed(
            session=self.session,
            bot=self.bot,
            rss_urls=self.rss_urls,
            keywords=self.keywords,
            embed_factory=self._create_news_embed,
            source_name="Hardwareluxx Hardware",
            guid_prefix="hlx_news",
            search_text_extractor=self._extract_search_text,
        )

    @check_rss_feed.before_loop
    async def before_rss_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Lädt das Hardwareluxx Hardware-News Cog"""
    await bot.add_cog(Hardwareluxx(bot))
    logger.info("Hardwareluxx News Cog geladen und RSS-Überwachung gestartet")
