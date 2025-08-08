"""
BIOS und UEFI Guides Cog für Loretta Bot
Enthält Kommandos für BIOS/UEFI/AGESA Übersichten
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.logging import log_command_success


logger = logging.getLogger(__name__)


class BiosCog(commands.Cog):
    """Cog für BIOS und UEFI Guides"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="bios", description="Link zu der besten AM4 BIOS Übersicht"
    )
    async def bios_guide(self, ctx: commands.Context) -> None:
        """Zeigt Link zur besten AM4/AM5 BIOS Übersicht"""
        log_command_success(logger, "bios", ctx.author, ctx.guild)

        embed = discord.Embed(
            title="Ultimative AM4 & AM5 UEFI/BIOS/AGESA Übersicht",
            colour=discord.Color.blurple(),
            description="Anbei findet ihr eine UEFI/BIOS Übersicht mit den jeweils aktuellsten Versionen, sortiert nach aktuellem AGESA Stand. Sollte mal eine Version fehlen oder ihr einen Fehler findet, dann dürft ihr das hier gerne mitteilen.\n[AM4](https://www.hardwareluxx.de/community/threads/ultimative-am4-uefi-bios-agesa-%C3%9Cbersicht-17-02-19.1228903/)\n[AM5](https://www.hardwareluxx.de/community/threads/am5-agesa-uefi-bios-info-laberthread.1323294/)\n\nChannel: <#578340164187979796>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url="https://i.imgur.com/ytFxJ9B.png")
        embed.set_thumbnail(url="https://i.imgur.com/6wqgd4K.png")
        embed.set_author(
            name="Reous (Mr. AMD)",
            url="https://www.hardwareluxx.de/community/members/reous.55847/",
            icon_url="https://i.imgur.com/ArBeYmq.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        try:
            await ctx.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"Fehler beim Senden der BIOS Guide Nachricht: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup-Funktion zum Hinzufügen des Cogs zum Bot"""
    await bot.add_cog(BiosCog(bot))
    logger.info("BIOS Cog geladen")
