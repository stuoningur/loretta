"""
Ping Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import time
import asyncio
import platform

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

        # Messe Internet-Latenz zu google.de
        internet_latency = await self._get_internet_latency()

        # Erstelle finales Embed
        embed = discord.Embed(
            title="Pong!",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
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

        internet_log = (
            f", Internet: {round(internet_latency)}ms"
            if internet_latency
            else ", Internet: N/A"
        )
        logger.info(
            f"Ping-Befehl ausgeführt von {ctx.author} "
            f"(WS: {round(websocket_latency)}ms, API: {round(api_latency)}ms{internet_log})"
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

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)

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
