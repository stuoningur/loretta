"""
Shutdown-Befehl für den Loretta Discord Bot
Enthält den graceful shutdown Befehl für Bot-Owner
"""

import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class Shutdown(commands.Cog):
    """Shutdown-Funktionalität für Bot-Verwaltung"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Überprüft ob der Benutzer Berechtigung für den Shutdown-Befehl hat"""
        return await self.bot.is_owner(ctx.author)

    @commands.hybrid_command(
        name="shutdown",
        description="Fährt den Bot kontrolliert herunter",
    )
    async def shutdown_bot(self, ctx):
        """Fährt den Bot kontrolliert herunter"""

        embed = discord.Embed(
            title="Bot wird heruntergefahren",
            description="Der Bot wird jetzt kontrolliert heruntergefahren...",
            color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)
        logger.info(f"Bot-Herunterfahren wurde von {ctx.author} initiiert")

        # Bot herunterfahren
        try:
            await self.bot.close()
        except Exception as e:
            logger.error(f"Fehler beim Herunterfahren: {e}")


async def setup(bot):
    """Lädt das Shutdown Cog"""
    await bot.add_cog(Shutdown(bot))
    logger.info("Shutdown Cog geladen")
