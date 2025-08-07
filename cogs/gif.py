"""
GIF Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import random
import aiohttp
import asyncio
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
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
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
                        
                        response = await api_request.json()
                        
            except (aiohttp.ClientConnectionError, aiohttp.ClientTimeout, asyncio.TimeoutError) as e:
                embed = discord.Embed(
                    title="Verbindungsfehler",
                    description="Konnte keine Verbindung zur Tenor API herstellen. Versuche es später erneut.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed.set_footer(
                    text=f"Angefordert von {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=embed)
                return
            except Exception as e:
                logger.error(f"Unerwarteter Fehler beim GIF-Abruf: {e}")
                embed = discord.Embed(
                    title="Fehler",
                    description="Ein unerwarteter Fehler ist aufgetreten. Versuche es später erneut.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed.set_footer(
                    text=f"Angefordert von {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=embed)
                return

            # Handle JSON parsing and response validation
            if not response or "results" not in response:
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

            gifs = []
            for gif in response["results"]:
                if "itemurl" in gif:
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


async def setup(bot):
    """Lädt das GIF Cog"""
    await bot.add_cog(Gif(bot))
    logger.info("GIF Cog geladen")