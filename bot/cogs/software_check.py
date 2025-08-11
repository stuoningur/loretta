"""
Software Check Cog für den Loretta Discord Bot
Überwacht den ComputerBase RSS-Feeds nach Software-Downloads
"""

import logging

import aiohttp
import discord
from discord.ext import commands, tasks

from bot.utils.embeds import EmbedFactory
from bot.utils.rss_feed import process_rss_feed
from utils.constants import SOFTWARE_KEYWORDS

logger = logging.getLogger(__name__)


class SoftwareCheck(commands.Cog):
    """Automatische Überwachung von Software-Downloads via RSS-Feed"""

    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.rss_urls = ["https://www.computerbase.de/rss/downloads.xml"]
        self.keywords = SOFTWARE_KEYWORDS

    async def cog_load(self):
        """Initialisiert die HTTP-Session und startet den RSS-Check"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self.check_rss_feed.start()

    async def cog_unload(self):
        """Stoppt die RSS-Überwachung und schließt die HTTP-Session"""
        self.check_rss_feed.cancel()
        if self.session:
            await self.session.close()
        logger.info("Software Check Cog entladen und RSS-Überwachung gestoppt")

    async def _create_news_embed(self, entry) -> discord.Embed:
        """Erstellt ein Embed für eine Software-Update"""
        return EmbedFactory.rss_news_embed(
            entry=entry,
            source="software",
            include_description=True,
            include_thumbnail=False,
            include_category=False,
        )

    @tasks.loop(minutes=15)
    async def check_rss_feed(self):
        """Überprüft den RSS-Feed alle 15 Minuten"""
        await process_rss_feed(
            session=self.session,
            bot=self.bot,
            rss_urls=self.rss_urls,
            keywords=self.keywords,
            embed_factory=self._create_news_embed,
            source_name="Software",
            guid_prefix="software",
        )

    @check_rss_feed.before_loop
    async def before_rss_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Lädt das Software Check Cog"""
    await bot.add_cog(SoftwareCheck(bot))
    logger.info("Software Check Cog geladen und RSS-Überwachung gestartet")
