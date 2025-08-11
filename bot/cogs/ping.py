"""
Ping Befehl für den Loretta Discord Bot
"""

import asyncio
import logging
import platform
import time

import discord
from discord.ext import commands

from bot.utils.decorators import track_command_usage
from bot.utils.embeds import EmbedFactory
from utils.logging import log_command_success

logger = logging.getLogger(__name__)


class Ping(commands.Cog):
    """Ping Befehl und Latenz-Informationen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Zeigt die Bot-Latenz an",
    )
    @track_command_usage
    async def ping(self, ctx):
        """Zeigt Ping-Informationen mit Latenz und API-Antwortzeit"""

        # Beginne Zeitmessung für API-Antwortzeit
        start_time = time.perf_counter()

        # Erstelle initial Embed für sofortige Antwort
        embed = EmbedFactory.info_command_embed(
            title="Pong!",
            description="Messe Latenz...",
            requester=ctx.author,
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

        # Messe Internet-Latenz zu google.de
        internet_latency = await self._get_internet_latency()

        # Erstelle finales Embed
        embed = EmbedFactory.info_command_embed(
            title="Pong!",
            description="",
            requester=ctx.author,
        )

        # Latenz-Informationen mit Internet-Latenz als erste Zeile (ohne Message Edit Time)
        if internet_latency:
            latency_info = f"**Internet (google.de):** {round(internet_latency)}ms\n"
        else:
            latency_info = "**Internet (google.de):** N/A\n"

        latency_info += (
            f"**WebSocket:** {round(websocket_latency)}ms\n"
            f"**API Antwort:** {round(api_latency)}ms"
        )

        embed.add_field(
            name="Latenz",
            value=latency_info,
            inline=False,
        )

        # Qualitätsbewertung basierend auf WebSocket-Latenz
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

        # Footer wird bereits durch info_command_embed gesetzt

        # Bearbeite die ursprüngliche Nachricht
        try:
            await message.edit(embed=embed)
        except (discord.HTTPException, discord.NotFound) as e:
            logger.error(f"Fehler beim Bearbeiten der Ping Nachricht: {e}")

        # Logging mit neuen Utility-Funktionen
        internet_log = f"{round(internet_latency)}ms" if internet_latency else "N/A"
        log_command_success(
            logger,
            "ping",
            ctx.author,
            ctx.guild,
            websocket_latency=f"{round(websocket_latency)}ms",
            api_latency=f"{round(api_latency)}ms",
            internet_latency=internet_log,
        )

    async def _get_internet_latency(self):
        """Misst Internet-Latenz durch Ping zu google.de"""
        try:
            # Ping-Befehl je nach Betriebssystem
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "4", "google.de"]
            else:
                cmd = ["ping", "-c", "4", "google.de"]

            # Führe Ping-Befehl asynchron aus
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5.0)

            if process.returncode == 0:
                # Parse Ping-Ausgabe für durchschnittliche Latenz
                output = stdout.decode()

                # Extrahiere durchschnittliche Latenz aus der Ausgabe
                if system == "windows":
                    # Windows Format: "Durchschnitt = XXXms"
                    for line in output.split("\n"):
                        if "Durchschnitt" in line or "Average" in line:
                            try:
                                # Extrahiere Zahl vor "ms"
                                parts = line.split("=")[-1].strip()
                                return float(parts.replace("ms", "").strip())
                            except (ValueError, IndexError):
                                continue
                else:
                    # Linux/Unix Format: "rtt min/avg/max/mdev = ..."
                    for line in output.split("\n"):
                        if "rtt min/avg/max/mdev" in line or "round-trip" in line:
                            try:
                                # Format: "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.123 ms"
                                parts = line.split("=")[-1].strip().split("/")
                                return float(parts[1])
                            except (ValueError, IndexError):
                                continue

        except (asyncio.TimeoutError, Exception) as e:
            logger.debug(f"Internet-Ping fehlgeschlagen: {e}")
            return None

        return None


async def setup(bot):
    """Lädt das Ping Cog"""
    await bot.add_cog(Ping(bot))
    logger.info("Ping Cog geladen")
