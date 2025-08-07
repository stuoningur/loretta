"""
Sgehdn Befehl für den Loretta Discord Bot
"""

from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class Sgehdn(commands.Cog):
    """Sgehdn Befehl für lustige GIF-Reaktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="sgehdn",
        description="Sendet ein Sgehdn GIF",
    )
    async def sgehdn(self, ctx):
        """Sendet das Sgehdn GIF von Tenor"""

        # Sende das GIF direkt
        await ctx.send("https://tenor.com/view/sgehdn-hi-hello-wave-greet-gif-17067641")

        logger.info(f"Sgehdn-Befehl ausgeführt von {ctx.author}")


async def setup(bot):
    """Lädt das Sgehdn Cog"""
    await bot.add_cog(Sgehdn(bot))
    logger.info("Sgehdn Cog geladen")
