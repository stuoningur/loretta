"""
GIF Befehl für den Loretta Discord Bot
"""

import asyncio
import logging
import os
import random

import aiohttp
from discord.ext import commands

from utils.decorators import track_command_usage
from utils.embeds import EmbedFactory
from utils.logging import log_command_error, log_command_success
from utils.responses import send_error_response, send_response

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
    @track_command_usage
    async def gif(self, ctx, *, arg: str):
        """Sucht die Top 30 GIFs für das Argument und gibt ein Ergebnis zufällig wieder"""

        try:
            if not self.tenor_api:
                await send_error_response(
                    ctx,
                    "Konfigurationsfehler",
                    "Tenor API-Schlüssel ist nicht konfiguriert.",
                )
                return

            lmt = 30
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout

            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"https://api.tenor.com/v1/search?q={arg}&key={self.tenor_api}&limit={lmt}"
                    async with session.get(url) as api_request:
                        if api_request.status != 200:
                            await send_error_response(
                                ctx,
                                "API Fehler",
                                "Fehler beim Suchen von GIFs. Versuche es später erneut.",
                            )
                            log_command_error(
                                logger,
                                "gif",
                                ctx.author,
                                ctx.guild,
                                Exception(
                                    f"Tenor API returned status {api_request.status}"
                                ),
                            )
                            return

                        response = await api_request.json()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                await send_error_response(
                    ctx,
                    "Verbindungsfehler",
                    "Konnte keine Verbindung zur Tenor API herstellen. Versuche es später erneut.",
                )
                log_command_error(logger, "gif", ctx.author, ctx.guild, e)
                return
            except Exception as e:
                await send_error_response(
                    ctx,
                    "Unerwarteter Fehler",
                    "Ein unerwarteter Fehler ist aufgetreten. Versuche es später erneut.",
                )
                log_command_error(logger, "gif", ctx.author, ctx.guild, e)
                return

            # Handle JSON parsing and response validation
            if not response or "results" not in response:
                embed = EmbedFactory.info_embed(
                    title="Keine GIFs gefunden",
                    description=f"Keine GIFs für '{arg}' gefunden.",
                )
                await send_response(ctx, embed)
                return

            gifs = []
            for gif in response["results"]:
                if "itemurl" in gif:
                    gifs.append(gif["itemurl"])

            if gifs:
                await ctx.send(random.choice(gifs))
                log_command_success(
                    logger,
                    "gif",
                    ctx.author,
                    ctx.guild,
                    search_term=arg,
                    results_count=len(gifs),
                )
            else:
                embed = EmbedFactory.info_embed(
                    title="Keine GIFs gefunden",
                    description=f"Keine GIFs für '{arg}' gefunden.",
                )
                await send_response(ctx, embed)

        except Exception as e:
            await send_error_response(
                ctx,
                "Fehler",
                "Ein Fehler ist beim Suchen von GIFs aufgetreten.",
            )
            log_command_error(logger, "gif", ctx.author, ctx.guild, e)


async def setup(bot):
    """Lädt das GIF Cog"""
    await bot.add_cog(Gif(bot))
    logger.info("GIF Cog geladen")
