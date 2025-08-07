"""
Screenshot Befehl für den Loretta Discord Bot
"""

from discord.ext import commands
import logging

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

        logger.info(f"Screenshot-Befehl ausgeführt von {ctx.author}")


async def setup(bot):
    """Lädt das Screenshot Cog"""
    await bot.add_cog(Screenshot(bot))
    logger.info("Screenshot Cog geladen")
