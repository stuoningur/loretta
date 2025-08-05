"""
Würfel Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import random

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
    async def roll(self, ctx, maximum: int = 100):
        """Würfelt eine Zufallszahl zwischen 1 und dem angegebenen Maximum"""

        try:
            # Validiere das Maximum
            if maximum < 1:
                embed = discord.Embed(
                    title="Fehler",
                    description="Das Maximum muss mindestens 1 sein.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )

                embed.set_footer(
                    text=f"Angefordert von {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url,
                )

                await ctx.send(embed=embed)
                return

            if maximum > 1000000:
                embed = discord.Embed(
                    title="Fehler",
                    description="Das Maximum darf nicht größer als 1.000.000 sein.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )

                embed.set_footer(
                    text=f"Angefordert von {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url,
                )

                await ctx.send(embed=embed)
                return

            # Würfle eine Zufallszahl
            result = random.randint(1, maximum)

            # Erstelle Erfolgs-Embed
            embed = discord.Embed(
                title="Würfel",
                description=f"Du hast eine **{result}** gewürfelt! (1-{maximum})",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

            logger.info(
                f"Würfel-Befehl ausgeführt von {ctx.author}: {result} (1-{maximum})"
            )

        except ValueError:
            embed = discord.Embed(
                title="Fehler",
                description="Bitte gib eine gültige Zahl ein.\n\nBeispiel: `/würfel 20`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Fehler beim Würfeln: {e}")

            embed = discord.Embed(
                title="Fehler",
                description="Beim Würfeln ist ein Fehler aufgetreten.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Roll Cog"""
    await bot.add_cog(Roll(bot))
    logger.info("Roll Cog geladen")
