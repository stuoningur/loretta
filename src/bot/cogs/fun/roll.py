"""
Würfel Befehl für den Loretta Discord Bot
"""

import logging
import random

from discord.ext import commands

from src.bot.utils.decorators import track_command_usage
from src.bot.utils.embeds import EmbedFactory
from src.bot.utils.logging import log_command_error, log_command_success
from src.bot.utils.responses import send_error_response, send_response

logger = logging.getLogger(__name__)


class Roll(commands.Cog):
    """Würfel Befehl für Zufallszahlen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="roll",
        aliases=["würfel"],
        description="Würfelt eine Zufallszahl (Standard: 1-100)",
    )
    @track_command_usage
    async def roll(self, ctx, maximum: int = 100):
        """Würfelt eine Zufallszahl zwischen 1 und dem angegebenen Maximum"""

        try:
            # Validiere das Maximum
            if maximum < 1:
                await send_error_response(
                    ctx, "Fehler", "Das Maximum muss mindestens 1 sein."
                )
                return

            if maximum > 1000000:
                await send_error_response(
                    ctx, "Fehler", "Das Maximum darf nicht größer als 1.000.000 sein."
                )
                return

            # Würfle eine Zufallszahl
            result = random.randint(1, maximum)

            # Erstelle Erfolgs-Embed
            embed = EmbedFactory.info_command_embed(
                title="Würfel",
                description=f"Du hast eine **{result}** gewürfelt! (1-{maximum})",
                requester=ctx.author,
            )

            await send_response(ctx, embed)
            log_command_success(
                logger, "roll", ctx.author, ctx.guild, result=result, maximum=maximum
            )

        except ValueError as e:
            await send_error_response(
                ctx,
                "Fehler",
                "Bitte gib eine gültige Zahl ein.\n\nBeispiel: `/würfel 20`",
            )
            log_command_error(logger, "roll", ctx.author, ctx.guild, e)

        except Exception as e:
            await send_error_response(
                ctx, "Fehler", "Beim Würfeln ist ein Fehler aufgetreten."
            )
            log_command_error(logger, "roll", ctx.author, ctx.guild, e)


async def setup(bot):
    """Lädt das Roll Cog"""
    await bot.add_cog(Roll(bot))
    logger.info("Roll Cog geladen")
