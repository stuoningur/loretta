"""
BIOS und UEFI Guides Cog für Loretta Bot
Enthält Kommandos für BIOS/UEFI/AGESA Übersichten
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class BiosCog(commands.Cog):
    """Cog für BIOS und UEFI Guides"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("BIOS Cog initialisiert")

    @commands.hybrid_command(
        name="bios", description="Link zu der besten AM4 BIOS Übersicht"
    )
    async def bios_guide(self, ctx: commands.Context) -> None:
        """Zeigt Link zur besten AM4/AM5 BIOS Übersicht"""
        logger.info(f"BIOS command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="Ultimative AM4 & AM5 UEFI/BIOS/AGESA Übersicht",
            colour=discord.Color.blurple(),
            description="Anbei findet ihr eine UEFI/BIOS Übersicht mit den jeweils aktuellsten Versionen, sortiert nach aktuellem AGESA Stand. Sollte mal eine Version fehlen oder ihr einen Fehler findet, dann dürft ihr das hier gerne mitteilen.\n[AM4](https://www.hardwareluxx.de/community/threads/ultimative-am4-uefi-bios-agesa-%C3%9Cbersicht-17-02-19.1228903/)\n[AM5](https://www.hardwareluxx.de/community/threads/am5-agesa-uefi-bios-info-laberthread.1323294/)\n\nChannel: <#578340164187979796>",
        )
        embed.set_image(url="https://i.imgur.com/ytFxJ9B.png")
        embed.set_thumbnail(url="https://i.imgur.com/6wqgd4K.png")
        embed.set_author(
            name="Reous (Mr. AMD)",
            url="https://www.hardwareluxx.de/community/members/reous.55847/",
            icon_url="https://i.imgur.com/ArBeYmq.png",
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot"""
    await bot.add_cog(BiosCog(bot))
