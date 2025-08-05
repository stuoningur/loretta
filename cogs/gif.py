"""
GIF Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import random
import aiohttp
import os

logger = logging.getLogger(__name__)


class Gif(commands.Cog):
    """GIF Befehl für das Suchen und Senden von GIFs"""

    def __init__(self, bot):
        self.bot = bot
        self.tenor_api = os.getenv("TENOR_API")

    @commands.hybrid_command(
        name="gif",
        aliases=["gifs"],
        description="Sucht die Top 30 GIFs für das Argument und gibt ein Ergebnis zufällig wieder",
    )
    async def gif(self, ctx, *, arg: str):
        """Sucht die Top 30 GIFs für das Argument und gibt ein Ergebnis zufällig wieder"""

        try:
            if not self.tenor_api:
                embed = discord.Embed(
                    title="Fehler",
                    description="Tenor API-Schlüssel ist nicht konfiguriert.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )

                embed.set_footer(
                    text=f"Angefordert von {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url,
                )

                await ctx.send(embed=embed)
                return

            lmt = 30
            async with aiohttp.ClientSession() as session:
                url = f"https://api.tenor.com/v1/search?q={arg}&key={self.tenor_api}&limit={lmt}"
                async with session.get(url) as api_request:
                    if api_request.status != 200:
                        embed = discord.Embed(
                            title="Fehler",
                            description="Fehler beim Suchen von GIFs. Versuche es später erneut.",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc),
                        )

                        embed.set_footer(
                            text=f"Angefordert von {ctx.author.display_name}",
                            icon_url=ctx.author.display_avatar.url,
                        )

                        await ctx.send(embed=embed)
                        return

                    gifs = []
                    top_gifs = await api_request.json()

                    if "results" not in top_gifs:
                        embed = discord.Embed(
                            title="Keine GIFs gefunden",
                            description=f"Keine GIFs für '{arg}' gefunden.",
                            color=discord.Color.orange(),
                            timestamp=datetime.now(timezone.utc),
                        )

                        embed.set_footer(
                            text=f"Angefordert von {ctx.author.display_name}",
                            icon_url=ctx.author.display_avatar.url,
                        )

                        await ctx.send(embed=embed)
                        return

                    for gif in top_gifs["results"]:
                        gifs.append(gif["itemurl"])

                    if gifs:
                        await ctx.send(random.choice(gifs))
                        logger.info(
                            f"GIF-Befehl ausgeführt von {ctx.author} mit Suchbegriff: '{arg}'"
                        )
                    else:
                        embed = discord.Embed(
                            title="Keine GIFs gefunden",
                            description=f"Keine GIFs für '{arg}' gefunden.",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc),
                        )

                        embed.set_footer(
                            text=f"Angefordert von {ctx.author.display_name}",
                            icon_url=ctx.author.display_avatar.url,
                        )

                        await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Fehler beim Suchen von GIFs: {e}")

            embed = discord.Embed(
                title="Fehler",
                description="Ein Fehler ist beim Suchen von GIFs aufgetreten.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)

    @gif.error
    async def gif_error(self, ctx, error):
        """Behandelt Fehler für den GIF-Befehl"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Fehler",
                description="Bitte gib einen Suchbegriff für das GIF ein.\n\nBeispiel: `/gif katze`",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )

            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.send(embed=embed)
        else:
            logger.error(f"Unerwarteter Fehler im GIF-Befehl: {error}")


async def setup(bot):
    """Lädt das GIF Cog"""
    await bot.add_cog(Gif(bot))
    logger.info("GIF Cog geladen")
