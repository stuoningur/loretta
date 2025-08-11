"""
Random Befehl für den Loretta Discord Bot
"""

import logging
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from bot.utils.decorators import track_command_usage

logger = logging.getLogger(__name__)


class Random(commands.Cog):
    """Random Befehl für zufällige Textmanipulation"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="random",
        description="Macht Text zufällig groß und klein",
    )
    @track_command_usage
    async def random(self, ctx, *, text: str):
        """Macht jeden Buchstaben im Text zufällig groß oder klein"""

        try:
            # Randomisiere die Groß-/Kleinschreibung
            randomized_text = "".join(
                char.upper() if random.choice([True, False]) else char.lower()
                for char in text
            )

            await ctx.send(randomized_text)

            logger.info(
                f"Random-Befehl ausgeführt von {ctx.author} mit Text: '{text[:50]}...'"
            )

        except Exception as e:
            logger.error(f"Fehler beim Randomisieren des Texts: {e}")

            # Erstelle Error Embed
            embed = discord.Embed(
                title="Fehler",
                description="Der Text konnte nicht randomisiert werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Random Cog"""
    await bot.add_cog(Random(bot))
    logger.info("Random Cog geladen")
