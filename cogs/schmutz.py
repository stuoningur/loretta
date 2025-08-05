"""
Schmutz Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
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

        try:
            # Sende das GIF direkt
            await ctx.send(
                "https://tenor.com/view/schmutz-dirt-filth-write-word-gif-16247714"
            )

            logger.info(f"Schmutz-Befehl ausgeführt von {ctx.author}")

        except discord.HTTPException as e:
            logger.error(f"Fehler beim Senden des Schmutz GIFs: {e}")

            # Erstelle Error Embed
            embed = discord.Embed(
                title="Fehler",
                description="Das Schmutz GIF konnte nicht gesendet werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Schmutz Cog"""
    await bot.add_cog(Schmutz(bot))
    logger.info("Schmutz Cog geladen")
