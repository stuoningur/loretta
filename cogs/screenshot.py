"""
Screenshot Befehl für den Loretta Discord Bot
"""

import logging

from discord.ext import commands

from utils.logging import log_command_success

logger = logging.getLogger(__name__)


class Screenshot(commands.Cog):
    """Screenshot Befehl für Bildschirmaufnahme-Hilfen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="screenshot",
        aliases=["ss", "winshifts", "bildschirmaufnahme"],
        description="Sendet ein Screenshot-Hilfe GIF",
    )
    async def screenshot(self, ctx):
        """Sendet das Screenshot-Hilfe GIF"""

        # Sende das GIF direkt
        await ctx.send("https://i.imgur.com/7wIUPkf.gif")

        log_command_success(logger, "screenshot", ctx.author, ctx.guild)


async def setup(bot):
    """Lädt das Screenshot Cog"""
    await bot.add_cog(Screenshot(bot))
    logger.info("Screenshot Cog geladen")
