"""
Bot-Informationen Befehl für den Loretta Discord Bot
"""

import logging
import platform
import time

import discord
import psutil
from discord.ext import commands

from src.bot.utils.decorators import track_command_usage
from src.bot.utils.embeds import EmbedFactory
from src.bot.utils.logging import BYTES_TO_GB_DIVISOR, log_command_success

# Constants
CPU_INTERVAL = 0.1
SECONDS_PER_DAY = 86400

logger = logging.getLogger(__name__)


class BotInfo(commands.Cog):
    """Bot-Informationen und Systemdaten"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="botinfo",
        description="Zeigt detaillierte Bot- und Systeminformationen an",
    )
    @track_command_usage
    async def botinfo(self, ctx):
        """Zeigt detaillierte Bot-Informationen mit System- und Statusdaten"""

        # Erstelle initial Embed
        embed = EmbedFactory.info_command_embed(
            title="Bot-Informationen",
            description="Lade Bot- und Systeminformationen...",
            requester=ctx.author,
        )

        # Sende initiale Nachricht
        message = await ctx.send(embed=embed)

        # Systeminformationen sammeln
        try:
            # CPU und Memory
            cpu_percent = psutil.cpu_percent(interval=CPU_INTERVAL)
            memory = psutil.virtual_memory()

            # System uptime berechnen
            system_uptime_seconds = time.time() - psutil.boot_time()
            system_uptime_days = int(system_uptime_seconds // SECONDS_PER_DAY)

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
            discord_version = "Unbekannt"
            python_version = "Unbekannt"

        # Erstelle detailliertes Embed
        embed = EmbedFactory.info_command_embed(
            title="Bot-Informationen",
            description="",
            requester=ctx.author,
            thumbnail_url=self.bot.user.display_avatar.url,
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
            memory_used = memory.used / BYTES_TO_GB_DIVISOR  # GB
            memory_total = memory.total / BYTES_TO_GB_DIVISOR  # GB
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

        # Thumbnail und Footer werden bereits durch info_command_embed gesetzt

        # Bearbeite die ursprüngliche Nachricht
        await message.edit(embed=embed)
        log_command_success(logger, "botinfo", ctx.author, ctx.guild)


async def setup(bot):
    """Lädt das BotInfo Cog"""
    await bot.add_cog(BotInfo(bot))
    logger.info("BotInfo Cog geladen")
