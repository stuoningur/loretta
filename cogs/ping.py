"""
Ping Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import time

logger = logging.getLogger(__name__)


class Ping(commands.Cog):
    """Ping Befehl und Latenz-Informationen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Zeigt die Bot-Latenz an",
    )
    async def ping(self, ctx):
        """Zeigt Ping-Informationen mit Latenz und API-Antwortzeit"""

        # Beginne Zeitmessung für API-Antwortzeit
        start_time = time.perf_counter()

        # Erstelle initial Embed für sofortige Antwort
        embed = discord.Embed(
            title="Pong!",
            description="Messe Latenz...",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Sende initiale Nachricht
        try:
            message = await ctx.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"Fehler beim Senden der Ping Nachricht: {e}")
            return

        # Berechne API-Antwortzeit
        end_time = time.perf_counter()
        api_latency = (end_time - start_time) * 1000

        # WebSocket-Latenz vom Bot
        websocket_latency = self.bot.latency * 1000

        # Erstelle finales Embed
        embed = discord.Embed(
            title="Pong!",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Latenz-Informationen
        latency_info = (
            f"**WebSocket:** {round(websocket_latency)}ms\n"
            f"**API Antwort:** {round(api_latency)}ms\n"
            f"**Nachricht Bearbeitung:** {round((time.perf_counter() - start_time) * 1000)}ms"
        )

        embed.add_field(
            name="Latenz",
            value=latency_info,
            inline=False,
        )

        # Qualitätsbewertung
        if websocket_latency < 50:
            quality = "Ausgezeichnet"
        elif websocket_latency < 100:
            quality = "Sehr gut"
        elif websocket_latency < 150:
            quality = "Gut"
        elif websocket_latency < 200:
            quality = "Akzeptabel"
        else:
            quality = "Langsam"

        embed.add_field(
            name="Verbindungsqualität",
            value=quality,
            inline=False,
        )

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        # Bearbeite die ursprüngliche Nachricht
        try:
            await message.edit(embed=embed)
        except (discord.HTTPException, discord.NotFound) as e:
            logger.error(f"Fehler beim Bearbeiten der Ping Nachricht: {e}")
        logger.info(
            f"Ping-Befehl ausgeführt von {ctx.author} "
            f"(WS: {round(websocket_latency)}ms, API: {round(api_latency)}ms)"
        )


async def setup(bot):
    """Lädt das Ping Cog"""
    await bot.add_cog(Ping(bot))
    logger.info("Ping Cog geladen")
