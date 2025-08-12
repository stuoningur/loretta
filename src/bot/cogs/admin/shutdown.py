"""
Shutdown-Befehl für den Loretta Discord Bot
Enthält den graceful shutdown Befehl für Bot-Owner
"""

import logging

from discord.ext import commands

from src.bot.utils.decorators import track_command_usage
from src.bot.utils.embeds import EmbedFactory
from src.bot.utils.logging import log_command_success

logger = logging.getLogger(__name__)


class Shutdown(commands.Cog):
    """Shutdown-Funktionalität für Bot-Verwaltung"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="shutdown",
        description="Fährt den Bot kontrolliert herunter",
    )
    @commands.is_owner()
    @track_command_usage
    async def shutdown_bot(self, ctx):
        """Fährt den Bot kontrolliert herunter"""

        embed = EmbedFactory.info_command_embed(
            title="Bot wird heruntergefahren",
            description="Der Bot wird jetzt kontrolliert heruntergefahren...",
            requester=ctx.author,
        )

        await ctx.send(embed=embed)
        log_command_success(logger, "shutdown", ctx.author, ctx.guild)

        # Bot herunterfahren
        try:
            await self.bot.close()
        except Exception as e:
            logger.error(f"Fehler beim Herunterfahren des Bots: {e}", exc_info=True)


async def setup(bot):
    """Lädt das Shutdown Cog"""
    await bot.add_cog(Shutdown(bot))
    logger.info("Shutdown Cog geladen")
