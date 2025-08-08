"""
RAM Guides Cog für Loretta Bot
Enthält alle RAM-bezogenen Kommandos (OC, Timings, SPD, etc.)
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands


logger = logging.getLogger(__name__)


class RamGuidesCog(commands.Cog):
    """Cog für RAM Overclocking und Guides"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="limit",
        aliases=["limits"],
        description="Link zu Hardwareluxx RAM OC und Limit Thread",
    )
    async def ram_limits(self, ctx: commands.Context) -> None:
        """Zeigt Link zu Hardwareluxx RAM OC und Limit Thread"""
        logger.info(f"Limit command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="Ryzen RAM OC Thread + Mögliche Limitierungen",
            colour=discord.Color.blurple(),
            url="https://www.hardwareluxx.de/community/threads/ryzen-ram-oc-thread-m%C3%B6gliche-limitierungen.1216557/",
            description="In diesem Thread werde ich Informationen zum Thema RAM OC Allgemein sammeln, sowie nennenswerte Anleitungen oder Threads verlinken. Habt ihr Fragen zum Thema RAM OC oder braucht Hilfe euren RAM zu übertakten, dann seid ihr hier im richtigen Thread. Zögert nicht zu fragen, wir helfen gerne weiter.\n\nChannel: <#506902038215655424>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url="https://i.imgur.com/isFPomg.png")
        embed.set_thumbnail(url="https://i.imgur.com/RZVRV7K.png")
        embed.set_author(
            name="Reous (Mr. AMD)",
            url="https://www.hardwareluxx.de/community/members/reous.55847/",
            icon_url="https://i.imgur.com/ArBeYmq.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="liste",
        aliases=["list", "ergebnisse"],
        description="Link zum OC Ergebnisse Google Sheet",
    )
    async def ram_results(self, ctx: commands.Context) -> None:
        """Zeigt Link zum OC Ergebnisse Google Sheet"""
        logger.info(f"Liste command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="RAM OC Ergebnisse - Google Sheet",
            colour=discord.Color.blurple(),
            url="https://docs.google.com/spreadsheets/d/1HKPVfDcFO-aieAOXHFQZp15rwWadbPTVDNgO8vtyDCM",
            description="Eine Sammlung an RAM OC Ergebnissen übersichtlich in einem Google Sheet dargestellt.\n\nChannel: <#590255495592542219>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url="https://i.imgur.com/14yKUIi.png")
        embed.set_thumbnail(url="https://i.imgur.com/OE94LR0.png")
        embed.set_author(
            name="shaav - Philipp",
            url="https://www.hardwareluxx.de/community/members/shaav.25323/",
            icon_url="https://i.imgur.com/DB4ei4M.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="anleitung",
        aliases=["manual"],
        description="Link zu der RAM OC Anleitung",
    )
    async def ram_manual(self, ctx: commands.Context) -> None:
        """Zeigt Link zur RAM OC Anleitung"""
        logger.info(f"Manual command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="RAM OC Anleitung",
            colour=discord.Color.blurple(),
            url="https://www.computerbase.de/forum/threads/amd-ryzen-ram-oc-community.1829356/",
            description="Wir versuchen nicht nur höhere RAM-Taktstufen zu erreichen, sondern auch die dazugehörigen Haupt- & Subtimings auf das System abgestimmt zu optimieren.",
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Download",
            value="[Link zur Zen2 PDF Anleitung - Version 2.20 (18.11.2020)](https://cdn.discordapp.com/attachments/506901533821239317/778530872700960778/RAM_OC_Anleitung_Vers_2_2.pdf)\n\n[Link zur Zen1/Zen+ PDF Anleitung - Version 1.30 (11.04.2019)](https://drive.google.com/open?id=1NQcR5ZiBnI-vENU-XSnQvvB3JzmGn2Ze)",
            inline=False,
        )
        embed.add_field(
            name="Wichtige RAM Timings von Reous",
            value="[RAM Timings und deren Einfluss auf Spiele und Anwendungen](https://www.hardwareluxx.de/community/threads/ram-timings-und-deren-einfluss-auf-spiele-und-anwendungen-amd.1269156/#5.0)\n\nChannel: <#590260218512932919>",
            inline=False,
        )
        embed.set_image(url="https://i.imgur.com/4hCP34S.png")
        embed.set_thumbnail(url="https://i.imgur.com/W83EAab.png")
        embed.set_author(
            name="cm87",
            url="https://www.computerbase.de/forum/members/cm87.771841/",
            icon_url="https://i.imgur.com/Fci12gO.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="ramkit",
        aliases=["ramkits", "ram"],
        description="Link zum Computerbase RAM-Empfehlungen Artikel",
    )
    async def ram_recommendations(self, ctx: commands.Context) -> None:
        """Zeigt Link zum Computerbase RAM-Empfehlungen Artikel"""
        logger.info(f"Ramkit command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="Aus der Community: RAM-Empfehlungen für AMD Ryzen und Intel Core",
            colour=discord.Color.blurple(),
            url="https://www.computerbase.de/thema/ram/rangliste/",
            description="In der Prozessor- und der Grafikkarten-Rangliste spricht ComputerBase bereits seit vier Jahren monatlich CPU- und GPU-Kaufempfehlungen aus. Ab sofort gibt es auch eine Kaufberatung für Arbeitsspeicher. Deren Pflege verantwortet die Community.\n\nChannel: <#612647199737774104>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url="https://i.imgur.com/pOsPkxk.png")
        embed.set_thumbnail(url="https://i.imgur.com/Iml7Mgn.png")
        embed.set_author(
            name="SV3N",
            url="https://www.computerbase.de/forum/members/sv3n.774722/",
            icon_url="https://i.imgur.com/cjo3SMD.png",
        )
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="spd", aliases=["ics"], description="Link zur HARDWARELUXX SPD Datenbank"
    )
    async def spd_database(self, ctx: commands.Context) -> None:
        """Zeigt Link zur HARDWARELUXX SPD Datenbank"""
        logger.info(f"SPD command ausgeführt von {ctx.author} in {ctx.guild}")

        embed = discord.Embed(
            title="Hardwareluxx SPD Datenbank",
            colour=discord.Color.blurple(),
            url="https://www.hardwareluxx.de/community/threads/hardwareluxx-spd-datenbank-anleitung-zum-ic-auslesen-v3-update-14-02-20.1073628/",
            description="Sammelthread auf Hardwareluxx für SPD Daten von DDR1 bis DDR4 inkl. Anleitung zum Auslesen der Daten.\n\nChannel: <#545701084409233438>",
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Siehe auch",
            value="[Hersteller IC Versionsnummern](https://i.imgur.com/sCc4l7l.png)",
            inline=False,
        )
        embed.set_image(url="https://i.imgur.com/OgacaAo.png")
        embed.set_thumbnail(url="https://i.imgur.com/yYBXwTP.png")
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
    await bot.add_cog(RamGuidesCog(bot))
    logger.info("RAM Guides Cog geladen")
