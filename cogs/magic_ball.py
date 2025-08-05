"""
Magic 8 Ball Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import random

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
            embed = discord.Embed(
                title="Magic 8 Ball",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.add_field(name="Frage", value=question, inline=False)

            embed.add_field(name="Antwort", value=answer, inline=False)

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

            logger.info(
                f"8ball-Befehl ausgeführt von {ctx.author} mit Frage: '{question[:50]}...'"
            )

        except Exception as e:
            logger.error(f"Fehler beim Ausführen des 8ball-Befehls: {e}")

            # Erstelle Error Embed
            embed = discord.Embed(
                title="Fehler",
                description="Die Magic 8 Ball konnte deine Frage nicht beantworten.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

    @magic_ball.error
    async def magic_ball_error(self, ctx, error):
        """Behandelt Fehler für den Magic 8 Ball-Befehl"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Fehler",
                description="Bitte stelle eine Frage für die Magic 8 Ball.\n\nBeispiel: `/8ball Wird es morgen regnen?`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)
        else:
            logger.error(f"Unerwarteter Fehler im 8ball-Befehl: {error}")


async def setup(bot):
    """Lädt das Magic Ball Cog"""
    await bot.add_cog(MagicBall(bot))
    logger.info("Magic Ball Cog geladen")
