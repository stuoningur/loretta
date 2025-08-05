"""
Screenshot Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
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

        try:
            # Sende das GIF direkt
            await ctx.send("https://i.imgur.com/7wIUPkf.gif")

            logger.info(f"Screenshot-Befehl ausgeführt von {ctx.author}")

        except discord.HTTPException as e:
            logger.error(f"Fehler beim Senden des Screenshot GIFs: {e}")

            # Erstelle Error Embed
            embed = discord.Embed(
                title="Fehler",
                description="Das Screenshot GIF konnte nicht gesendet werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Screenshot Cog"""
    await bot.add_cog(Screenshot(bot))
    logger.info("Screenshot Cog geladen")
