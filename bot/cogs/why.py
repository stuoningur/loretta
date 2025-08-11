"""
Why Befehl für den Loretta Discord Bot
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from bot.utils.decorators import track_command_usage
from utils.logging import log_command_success

logger = logging.getLogger(__name__)


class Why(commands.Cog):
    """Why Befehl - Erklärt den Namen des Bots"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="why",
        aliases=["warum"],
        description="Erklärt den Namen des Bots",
    )
    @track_command_usage
    async def why(self, ctx):
        """Erklärt den Namen des Bots"""

        try:
            embed = discord.Embed(
                title="Das Leben des Brian",
                colour=discord.Color.blurple(),
                url="https://www.youtube.com/watch?v=GryQiamGxpY",
                description="Das Leben des Brian ist eine beißende Persiflage auf die schwülstigen Hollywood-Verfilmungen von Bibelthemen vorangegangener Jahre und karikiert auch viele gesellschaftliche Phänomene wie beispielsweise religiösen oder politischen Fanatismus.",
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_image(url="https://i.imgur.com/oJfFnzj.png")
            embed.set_thumbnail(url="https://i.imgur.com/BmHab8v.png")
            embed.set_author(
                name="Monty Python",
                url="https://de.wikipedia.org/wiki/Monty_Python",
                icon_url="https://i.imgur.com/1l78cyO.jpg",
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

            log_command_success(logger, "why", ctx.author, ctx.guild)

        except Exception as e:
            logger.error(f"Fehler beim Ausführen des Why-Befehls: {e}")

            # Erstelle Error Embed
            error_embed = discord.Embed(
                title="Fehler",
                description="Der Why-Befehl konnte nicht ausgeführt werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            error_embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=error_embed)


async def setup(bot):
    """Lädt das Why Cog"""
    await bot.add_cog(Why(bot))
    logger.info("Why Cog geladen")
