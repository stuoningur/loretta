"""
Sgehdn Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
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

        try:
            # Sende das GIF direkt
            await ctx.send(
                "https://tenor.com/view/sgehdn-hi-hello-wave-greet-gif-17067641"
            )

            logger.info(f"Sgehdn-Befehl ausgeführt von {ctx.author}")

        except discord.HTTPException as e:
            logger.error(f"Fehler beim Senden des Sgehdn GIFs: {e}")

            # Erstelle Error Embed
            embed = discord.Embed(
                title="Fehler",
                description="Das Sgehdn GIF konnte nicht gesendet werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Sgehdn Cog"""
    await bot.add_cog(Sgehdn(bot))
    logger.info("Sgehdn Cog geladen")
