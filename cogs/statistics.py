"""
Command-Statistiken Befehle für den Loretta Discord Bot
"""

import logging
from typing import Optional

from discord import app_commands
from discord.ext import commands

from utils.decorators import track_command_usage
from utils.embeds import EmbedFactory
from utils.logging import log_command_error, log_command_success
from utils.user_resolver import UserResolver

logger = logging.getLogger(__name__)


class Statistics(commands.Cog):
    """Command-Statistiken und Nutzungsanalysen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="stats",
        description="Zeigt Server-Command-Statistiken an",
    )
    @app_commands.describe(tage="Anzahl Tage rückblickend (Standard: 30)")
    @track_command_usage
    async def server_stats(self, ctx, tage: int = 30):
        """Zeigt Command-Statistiken für den Server an"""
        if not ctx.guild:
            embed = EmbedFactory.error_embed(
                "Fehler", "Dieser Befehl kann nur in einem Server verwendet werden."
            )
            await ctx.send(embed=embed)
            return

        # Validiere Tage-Parameter
        if tage < 1 or tage > 365:
            embed = EmbedFactory.error_embed(
                "Ungültiger Zeitraum",
                "Die Anzahl der Tage muss zwischen 1 und 365 liegen.",
            )
            await ctx.send(embed=embed)
            return

        try:
            # Hole Statistiken aus der Datenbank
            stats = await self.bot.db.get_command_statistics_summary(ctx.guild.id, tage)

            # Erstelle Embed
            embed = EmbedFactory.info_command_embed(
                title="Server Command-Statistiken",
                description=f"Statistiken der letzten {tage} Tage",
                requester=ctx.author,
            )

            # Grundlegende Statistiken
            embed.add_field(
                name="Gesamt-Übersicht",
                value=(
                    f"**Gesamt Commands:** {stats['total_commands']:,}\n"
                    f"**Erfolgreiche Commands:** {stats['successful_commands']:,}\n"
                    f"**Fehlgeschlagene Commands:** {stats['failed_commands']:,}\n"
                    f"**Erfolgsrate:** {stats['success_rate']:.1f}%"
                ),
                inline=False,
            )

            # Top Commands
            if stats["top_commands"]:
                top_commands_text = ""
                for i, (command, count) in enumerate(stats["top_commands"][:5], 1):
                    top_commands_text += f"{i}. `{command}` - {count:,}x\n"

                embed.add_field(
                    name="Meistgenutzte Commands",
                    value=top_commands_text,
                    inline=True,
                )

            # Top Users (nur User-IDs zu Mentions konvertieren falls möglich)
            if stats["top_users"]:
                top_users_text = ""
                for i, (user_id, count) in enumerate(stats["top_users"][:5], 1):
                    try:
                        user = self.bot.get_user(user_id) or await self.bot.fetch_user(
                            user_id
                        )
                        user_display = (
                            f"{user.display_name}" if user else f"Unbekannt ({user_id})"
                        )
                    except Exception:
                        user_display = f"Unbekannt ({user_id})"

                    top_users_text += f"{i}. {user_display} - {count:,}x\n"

                embed.add_field(
                    name="Aktivste Benutzer", value=top_users_text, inline=True
                )

            # Wenn keine Daten vorhanden sind
            if stats["total_commands"] == 0:
                embed.description = (
                    f"Keine Command-Daten für die letzten {tage} Tage gefunden."
                )

            await ctx.send(embed=embed)
            log_command_success(logger, "stats", ctx.author, ctx.guild, days=tage)

        except Exception as e:
            log_command_error(logger, "stats", ctx.author, ctx.guild, e, days=tage)
            embed = EmbedFactory.error_embed(
                "Fehler", "Beim Abrufen der Statistiken ist ein Fehler aufgetreten."
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="mystats",
        description="Zeigt deine persönlichen Command-Statistiken an",
    )
    @app_commands.describe(
        user="Benutzer dessen Statistiken angezeigt werden sollen (optional)",
        tage="Anzahl Tage rückblickend (Standard: 30)",
    )
    @track_command_usage
    async def user_stats(self, ctx, user: Optional[str] = None, tage: int = 30):
        """Zeigt persönliche Command-Statistiken eines Benutzers an"""
        if not ctx.guild:
            embed = EmbedFactory.error_embed(
                "Fehler", "Dieser Befehl kann nur in einem Server verwendet werden."
            )
            await ctx.send(embed=embed)
            return

        # Validiere Tage-Parameter
        if tage < 1 or tage > 365:
            embed = EmbedFactory.error_embed(
                "Ungültiger Zeitraum",
                "Die Anzahl der Tage muss zwischen 1 und 365 liegen.",
            )
            await ctx.send(embed=embed)
            return

        # Bestimme Ziel-Benutzer
        if user is None:
            target_user = ctx.author
        else:
            target_user = await UserResolver.resolve_user(ctx, user)
            if not target_user:
                return

        try:
            # Hole Benutzer-Statistiken aus der Datenbank
            stats = await self.bot.db.get_user_command_statistics(
                ctx.guild.id, target_user.id, tage
            )

            # Erstelle Embed
            is_self = target_user.id == ctx.author.id
            title = (
                "Meine Command-Statistiken"
                if is_self
                else f"Command-Statistiken von {target_user.display_name}"
            )

            embed = EmbedFactory.info_command_embed(
                title=title,
                description=f"Statistiken der letzten {tage} Tage",
                requester=ctx.author,
                thumbnail_url=target_user.display_avatar.url,
            )

            # Grundlegende Statistiken
            embed.add_field(
                name="Übersicht",
                value=(
                    f"**Gesamt Commands:** {stats['total_commands']:,}\n"
                    f"**Erfolgreiche Commands:** {stats['successful_commands']:,}\n"
                    f"**Fehlgeschlagene Commands:** {stats['failed_commands']:,}\n"
                    f"**Erfolgsrate:** {stats['success_rate']:.1f}%"
                ),
                inline=False,
            )

            # Server-Rang
            if stats["server_rank"] and stats["total_server_users"] > 0:
                embed.add_field(
                    name="Server-Rang",
                    value=f"**Rang:** #{stats['server_rank']} von {stats['total_server_users']} aktiven Benutzern",
                    inline=True,
                )

            # Meistgenutzte Commands
            if stats["commands_used"]:
                commands_text = ""
                for i, (command, count) in enumerate(stats["commands_used"][:8], 1):
                    commands_text += f"{i}. `{command}` - {count:,}x\n"

                embed.add_field(
                    name="Meistgenutzte Commands", value=commands_text, inline=True
                )

            # Wenn keine Daten vorhanden sind
            if stats["total_commands"] == 0:
                user_name = "Du hast" if is_self else f"{target_user.display_name} hat"
                embed.description = (
                    f"{user_name} in den letzten {tage} Tagen keine Commands verwendet."
                )

            await ctx.send(embed=embed)
            log_command_success(
                logger,
                "mystats",
                ctx.author,
                ctx.guild,
                target_user=target_user.name,
                days=tage,
            )

        except Exception as e:
            log_command_error(
                logger,
                "mystats",
                ctx.author,
                ctx.guild,
                e,
                target_user=target_user.name,
                days=tage,
            )
            embed = EmbedFactory.error_embed(
                "Fehler",
                "Beim Abrufen der Benutzer-Statistiken ist ein Fehler aufgetreten.",
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Statistics Cog"""
    await bot.add_cog(Statistics(bot))
    logger.info("Statistics Cog geladen")
