"""
Mainboard Guides Cog für Loretta Bot
Enthält Kommandos für Motherboard und VRM Guides
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.logging import log_command_success


logger = logging.getLogger(__name__)


class MainboardCog(commands.Cog):
    """Cog für Motherboard und VRM Guides"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mainboard",
        aliases=["mobo", "motherboard", "vrm"],
        description="Link zum Hardwareluxx AM4 VRM Thread",
    )
    async def mainboard_guide(self, ctx: commands.Context) -> None:
        """Zeigt Link zum Hardwareluxx AM4 VRM Thread"""
        log_command_success(logger, "mainboard", ctx.author, ctx.guild)

        embed = discord.Embed(
            title="AMD 3rd Gen AM4 Mainboards & VRM Liste (X570, P560, B550, A520, A420)",
            colour=discord.Color.blurple(),
            url="https://www.hardwareluxx.de/community/threads/amd-3rd-gen-am4-mainboards-vrm-liste-x570-p560-b550-a520-a420.1228904/",
            description="Hier dürfen News und Produkte diskutiert, Informationen erfragt und zusammengetragen, technische Fragen gestellt und schließlich auch Erfahrungen mit dem eigenen System ausgetauscht werden. Der Umfang des Threads hängt von eurer Beteiligung ab und eure Unterstützung beim Sammeln von Informationen zur Vervollständigung der Übersicht ist ausdrücklich erbeten.\n\nChannel: <#578340164187979796>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url="https://i.imgur.com/owYHwzW.jpg")
        embed.set_thumbnail(url="https://i.imgur.com/Motc8J6.png")
        embed.set_author(
            name="emissary42",
            url="https://www.hardwareluxx.de/community/members/emissary42.38573/",
            icon_url="https://i.imgur.com/DcfAykw.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot"""
    await bot.add_cog(MainboardCog(bot))
    logger.info("Mainboard Cog geladen")
