"""
Schmutz Befehl für den Loretta Discord Bot
"""

from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class Schmutz(commands.Cog):
    """Schmutz Befehl für lustige GIF-Reaktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="schmutz",
        description="Sendet ein Schmutz GIF",
    )
    async def schmutz(self, ctx):
        """Sendet das Schmutz GIF von Tenor"""

        # Sende das GIF direkt
        await ctx.send(
            "https://tenor.com/view/schmutz-dirt-filth-write-word-gif-16247714"
        )

        logger.info(f"Schmutz-Befehl ausgeführt von {ctx.author}")


async def setup(bot):
    """Lädt das Schmutz Cog"""
    await bot.add_cog(Schmutz(bot))
    logger.info("Schmutz Cog geladen")
