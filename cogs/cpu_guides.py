"""
CPU Guides Cog für Loretta Bot
Enthält Kommandos für CPU Optimierung und Curve Optimizer
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class CpuGuidesCog(commands.Cog):
    """Cog für CPU Optimierung und Guides"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("CPU Guides Cog initialisiert")

    @commands.hybrid_command(
        name="cpu", description="Link zu dem Community CPU und Bios Guide"
    )
    async def cpu_guide(self, ctx: commands.Context) -> None:
        """Zeigt Link zum Community CPU und BIOS Guide"""
        logger.info(f"CPU command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="CPU und BIOS Guide für Ryzen 3000 (und älter)",
            colour=discord.Color.blurple(),
            url="https://www.computerbase.de/forum/threads/cpu-und-bios-guide-fuer-ryzen-3000-und-aelter.1911429/",
            description="Erklärungen und Tipps um das beste aus einer AMD Ryzen CPU rauszuholen.\n\nChannel: <#612647199737774104>",
        )
        embed.set_image(url="https://i.imgur.com/jC0K8W8.png")
        embed.set_thumbnail(url="https://i.imgur.com/vVeSNQS.png")
        embed.set_author(
            name="Verangry",
            url="https://www.computerbase.de/forum/members/verangry.798158/",
            icon_url="https://i.imgur.com/mu0em6U.png",
        )

        try:
            await ctx.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"Fehler beim Senden der CPU Guide Nachricht: {e}")

    @commands.hybrid_command(
        name="curve",
        aliases=["co", "curveoptimizer", "kurvenoptimierer"],
        description="Link zu dem Community Curve Optimizer Guide",
    )
    async def curve_optimizer_guide(self, ctx: commands.Context) -> None:
        """Zeigt Link zum Community Curve Optimizer Guide"""
        logger.info(f"Curve command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="Curve Optimizer Guide Ryzen 5000",
            colour=discord.Color.blurple(),
            url="https://www.computerbase.de/forum/threads/curve-optimizer-guide-ryzen-5000.2015251/",
            description="Anleitung und Erklärungen für den Curve Optimizer bei Zen 3.\n\nChannel: <#612647199737774104>",
        )
        embed.add_field(
            name="PDF Download",
            value="[Link zur Curve Optimizer PDF Anleitung](https://drive.google.com/file/d/1EiVoPjuyaVKlzsL4sUsXwwVUVnch8QdR/view)",
            inline=False,
        )
        embed.set_image(url="https://i.imgur.com/jC0K8W8.png")
        embed.set_thumbnail(url="https://i.imgur.com/D5bEWL2.png")
        embed.set_author(
            name="Verangry",
            url="https://www.computerbase.de/forum/members/verangry.798158/",
            icon_url="https://i.imgur.com/mu0em6U.png",
        )

        try:
            await ctx.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"Fehler beim Senden der CPU Guide Nachricht: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot"""
    await bot.add_cog(CpuGuidesCog(bot))
