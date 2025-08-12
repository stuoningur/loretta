"""
Sgehdn Befehl für den Loretta Discord Bot
"""

import logging

from discord.ext import commands

from src.bot.utils.decorators import track_command_usage
from src.bot.utils.logging import log_command_success

logger = logging.getLogger(__name__)


class Sgehdn(commands.Cog):
    """Sgehdn Befehl für lustige GIF-Reaktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="sgehdn",
        description="Sendet ein Sgehdn GIF",
    )
    @track_command_usage
    async def sgehdn(self, ctx):
        """Sendet das Sgehdn GIF von Tenor"""

        # Sende das GIF direkt
        await ctx.send("https://tenor.com/view/sgehdn-hi-hello-wave-greet-gif-17067641")

        log_command_success(logger, "sgehdn", ctx.author, ctx.guild)


async def setup(bot):
    """Lädt das Sgehdn Cog"""
    await bot.add_cog(Sgehdn(bot))
    logger.info("Sgehdn Cog geladen")
