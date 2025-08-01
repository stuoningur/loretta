"""
Ping Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import time
import psutil
import platform

logger = logging.getLogger(__name__)


class Ping(commands.Cog):
    """Ping Befehl und Latenz-Informationen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Zeigt detaillierte Latenz- und Systeminformationen an",
    )
    async def ping(self, ctx):
        """Zeigt detaillierte Ping-Informationen mit Latenz, API-Antwortzeit und Systemdaten"""

        # Beginne Zeitmessung für API-Antwortzeit
        start_time = time.perf_counter()

        # Erstelle initial Embed für sofortige Antwort
        embed = discord.Embed(
            title="Pong!",
            description="Messe Latenz und lade Systeminformationen...",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Sende initiale Nachricht
        message = await ctx.send(embed=embed)

        # Berechne API-Antwortzeit
        end_time = time.perf_counter()
        api_latency = (end_time - start_time) * 1000

        # WebSocket-Latenz vom Bot
        websocket_latency = self.bot.latency * 1000

        # Systeminformationen sammeln
        try:
            # CPU und Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # System uptime berechnen
            system_uptime_seconds = time.time() - psutil.boot_time()
            system_uptime_days = int(system_uptime_seconds // 86400)

            # Discord.py Version
            discord_version = discord.__version__
            python_version = platform.python_version()
            system_info = f"{platform.system()} {platform.release()}"

        except Exception as e:
            logger.warning(f"Fehler beim Sammeln der Systeminformationen: {e}")
            cpu_percent = 0
            memory = None
            system_info = "Unbekannt"

        # Erstelle detailliertes Embed
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
            inline=True,
        )

        # Bot-Informationen
        bot_info = (
            f"**System Laufzeit:** {system_uptime_days} Tage\n"
            f"**Server:** {len(self.bot.guilds):,}\n"
            f"**Benutzer:** {len(set(self.bot.get_all_members())):,}"
        )

        embed.add_field(
            name="Bot Status",
            value=bot_info,
            inline=True,
        )

        # System-Informationen
        if memory:
            memory_used = memory.used / 1024**3  # GB
            memory_total = memory.total / 1024**3  # GB
            memory_percent = memory.percent

            system_info_text = (
                f"**CPU:** {cpu_percent:.1f}%\n"
                f"**RAM:** {memory_used:.1f}GB / {memory_total:.1f}GB ({memory_percent:.1f}%)\n"
                f"**System:** {system_info}"
            )
        else:
            system_info_text = f"**System:** {system_info}\n**Status:** Systeminformationen nicht verfügbar"

        embed.add_field(
            name="System",
            value=system_info_text,
            inline=False,
        )

        # Versions-Informationen
        version_info = (
            f"**Discord.py:** {discord_version}\n"
            f"**Python:** {python_version}\n"
            f"**Plattform:** {platform.machine()}"
        )

        embed.add_field(
            name="Versionen",
            value=version_info,
            inline=True,
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
            inline=True,
        )

        # Shard-Informationen (falls mehrere Shards verwendet werden)
        if self.bot.shard_count and self.bot.shard_count > 1:
            shard_info = f"**Shard:** {ctx.guild.shard_id + 1 if ctx.guild else 'N/A'} / {self.bot.shard_count}"
            embed.add_field(
                name="Shard",
                value=shard_info,
                inline=True,
            )

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        try:
            # Bearbeite die ursprüngliche Nachricht
            await message.edit(embed=embed)
            logger.info(
                f"Ping-Befehl ausgeführt von {ctx.author} "
                f"(WS: {round(websocket_latency)}ms, API: {round(api_latency)}ms)"
            )
        except discord.HTTPException as e:
            logger.error(f"Fehler beim Bearbeiten der Ping-Nachricht: {e}")
            await ctx.send("Fehler beim Anzeigen der Ping-Informationen.")


async def setup(bot):
    """Lädt das Ping Cog"""
    await bot.add_cog(Ping(bot))
    logger.info("Ping Cog geladen")
