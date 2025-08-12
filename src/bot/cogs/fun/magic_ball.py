"""
Magic 8 Ball Befehl für den Loretta Discord Bot
"""

import logging
import random

from discord.ext import commands

from src.bot.utils.decorators import track_command_usage
from src.bot.utils.embeds import EmbedFactory
from src.bot.utils.logging import log_command_error, log_command_success
from src.bot.utils.responses import send_error_response, send_response

logger = logging.getLogger(__name__)


class MagicBall(commands.Cog):
    """Magic 8 Ball Befehl für zufällige Antworten auf Fragen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Gibt eine Magic 8 Ball Antwort auf eine Frage",
        aliases=["magicball", "loretta"],
    )
    @track_command_usage
    async def magic_ball(self, ctx, *, question: str):
        """Gibt eine Magic 8 Ball Antwort auf eine Frage zurück"""

        try:
            responses = [
                "Das ist sicher.",
                "Es ist entschieden.",
                "Ohne Zweifel.",
                "Ja - definitiv.",
                "Du kannst dich darauf verlassen.",
                "So wie ich das sehe, ja.",
                "Höchstwahrscheinlich.",
                "Die Aussichten sind gut.",
                "Ja.",
                "Die Anzeichen deuten auf ein Ja.",
                "Antwort verschwommen - Versuch es noch einmal.",
                "Frage später noch einmal.",
                "Sage es dir besser nicht jetzt.",
                "Vorhersage jetzt nicht möglich.",
                "Konzentriere dich und frag noch einmal.",
                "Verlass dich nicht darauf.",
                "Meine Antwort ist nein.",
                "Meine Quellen sagen nein.",
                "Die Aussichten sind nicht so gut.",
                "Sehr zweifelhaft.",
            ]

            # Wähle eine zufällige Antwort
            answer = random.choice(responses)

            # Erstelle ein Embed für die Antwort
            embed = EmbedFactory.info_command_embed(
                title="Magic 8 Ball",
                description="",
                requester=ctx.author,
            )

            embed.add_field(name="Frage", value=question, inline=False)
            embed.add_field(name="Antwort", value=answer, inline=False)

            await send_response(ctx, embed)
            log_command_success(
                logger,
                "8ball",
                ctx.author,
                ctx.guild,
                question=question[:50] + ("..." if len(question) > 50 else ""),
                answer=answer,
            )

        except Exception as e:
            await send_error_response(
                ctx, "Fehler", "Die Magic 8 Ball konnte deine Frage nicht beantworten."
            )
            log_command_error(logger, "8ball", ctx.author, ctx.guild, e)


async def setup(bot):
    """Lädt das Magic Ball Cog"""
    await bot.add_cog(MagicBall(bot))
    logger.info("Magic Ball Cog geladen")
