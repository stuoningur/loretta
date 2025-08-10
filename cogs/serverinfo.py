"""
Serverinfo Befehle für den Loretta Discord Bot
"""

import logging

import discord
from discord.ext import commands

from utils.decorators import track_command_usage
from utils.embeds import EmbedFactory
from utils.logging import log_command_success
from utils.responses import send_error_response

logger = logging.getLogger(__name__)


class ServerInfo(commands.Cog):
    """Serverinfo Befehle und Funktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="serverinfo",
        description="Zeigt Informationen über den aktuellen Server an",
    )
    @track_command_usage
    async def serverinfo(self, ctx):
        """Zeigt detaillierte Informationen über den Server an"""
        if not ctx.guild:
            await send_error_response(
                ctx,
                "Nur auf Servern verfügbar",
                "Dieser Befehl kann nur auf einem Server verwendet werden!",
            )
            return

        guild = ctx.guild

        # Server-Erstellungsdatum
        created_at = guild.created_at

        # Mitglieder-Statistiken
        total_members = guild.member_count

        # Online-Status zählen (nur wenn Presences Intent aktiv ist)
        online_members = 0
        idle_members = 0
        dnd_members = 0
        offline_members = 0

        for member in guild.members:
            if member.status == discord.Status.online:
                online_members += 1
            elif member.status == discord.Status.idle:
                idle_members += 1
            elif member.status == discord.Status.dnd:
                dnd_members += 1
            else:
                offline_members += 1

        # Online zusammenfassen
        active_members = online_members + idle_members + dnd_members

        # Detaillierte Kanal-Statistiken
        text_channels = len(
            [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        )
        voice_channels = len(
            [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
        )
        stage_channels = len(
            [c for c in guild.channels if isinstance(c, discord.StageChannel)]
        )
        categories = len(
            [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]
        )
        forum_channels = len(
            [c for c in guild.channels if isinstance(c, discord.ForumChannel)]
        )
        total_channels = len(guild.channels)

        # Erstelle Embed
        embed = EmbedFactory.info_command_embed(
            title="Server Informationen",
            description="",
            requester=ctx.author,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

        # Thumbnail wird bereits durch info_command_embed gesetzt

        # Server-Grundinformationen (Name, ID, Besitzer)
        embed.add_field(
            name="",
            value=f"**Name:** {guild.name} (**ID:** {guild.id})\n"
            f"**Besitzer:** {guild.owner.display_name}\n"
            f"**Erstellt:** <t:{int(created_at.timestamp())}:R>\n"
            f"**Boost Level:** {guild.premium_tier}\n"
            f"**Anzahl Boosts:** {guild.premium_subscription_count}",
            inline=False,
        )

        # Rollen (ohne Server Booster und @everyone) und Mitglieder Status
        embed.add_field(
            name="",
            value=f"**Server Rollen:** {len(guild.roles) - 2:,}\n"
            f"**Mitglieder Online:** {active_members:,}\n**Mitglieder Offline:** {offline_members:,}",
            inline=False,
        )

        # Linke Spalte - Mitglieder Details
        # Top-Rollen nach Mitgliederzahl (Top 10, ohne @everyone und Server Booster)
        top_roles = []
        for role in sorted(guild.roles, key=lambda r: len(r.members), reverse=True):
            if (
                len(role.members) > 0
                and role.name.lower() != "server booster"
                and role.name != "@everyone"
                and len(top_roles) < 10
            ):
                top_roles.append(f"{role.name}: {len(role.members)}")

        left_column = f"**Mitglieder: {total_members:,}**\n"
        if top_roles:
            left_column += "\n".join(top_roles)

        embed.add_field(
            name="",
            value=left_column,
            inline=True,
        )

        # Rechte Spalte - Kanal Details
        right_column = f"**Kanäle: {total_channels:,}**\n"
        right_column += f"Kategorien: {categories:,}\n"
        right_column += f"Text: {text_channels:,}\n"
        if forum_channels > 0:
            right_column += f"Forum: {forum_channels:,}\n"
        right_column += f"Sprach: {voice_channels:,}"
        if stage_channels > 0:
            right_column += f"Bühne_Sprach: {stage_channels:,}\n"

        embed.add_field(
            name="",
            value=right_column,
            inline=True,
        )

        # Footer wird bereits durch info_command_embed gesetzt

        await ctx.send(embed=embed)
        log_command_success(logger, "serverinfo", ctx.author, ctx.guild)


async def setup(bot):
    """Lädt das ServerInfo Cog"""
    await bot.add_cog(ServerInfo(bot))
    logger.info("ServerInfo Cog geladen")
