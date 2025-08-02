"""
Bot-Informationen Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import time
import psutil
import platform

logger = logging.getLogger(__name__)


class BotInfo(commands.Cog):
    """Bot-Informationen und Systemdaten"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="botinfo",
        description="Zeigt detaillierte Bot- und Systeminformationen an",
    )
    async def botinfo(self, ctx):
        """Zeigt detaillierte Bot-Informationen mit System- und Statusdaten"""

        # Erstelle initial Embed
        embed = discord.Embed(
            title="Bot-Informationen",
            description="Lade Bot- und Systeminformationen...",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )

        # Sende initiale Nachricht
        message = await ctx.send(embed=embed)

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
            system_uptime_days = 0

        # Erstelle detailliertes Embed
        embed = discord.Embed(
            title="Bot-Informationen",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
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
            inline=True,
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
            inline=False,
        )

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        try:
            # Bearbeite die ursprüngliche Nachricht
            await message.edit(embed=embed)
            logger.info(f"BotInfo-Befehl ausgeführt von {ctx.author}")
        except discord.HTTPException as e:
            logger.error(f"Fehler beim Bearbeiten der BotInfo-Nachricht: {e}")
            await ctx.send("Fehler beim Anzeigen der Bot-Informationen.")


async def setup(bot):
    """Lädt das BotInfo Cog"""
    await bot.add_cog(BotInfo(bot))
    logger.info("BotInfo Cog geladen")
