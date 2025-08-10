"""
Member Log Cog für den Loretta Discord Bot
Protokolliert Member Join/Leave Events
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class MemberLogCog(commands.Cog):
    """Cog für das Protokollieren von Member-Events"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Event Handler für Member Join"""
        try:
            if not member.guild:
                return

            # Hole Server-Konfiguration
            config = await self.bot.db.get_guild_config(member.guild.id)

            # Prüfe ob Log-Kanal konfiguriert ist
            if not config.log_channel_id:
                return

            # Hole Log-Kanal
            log_channel = member.guild.get_channel(config.log_channel_id)
            if not log_channel or not isinstance(log_channel, discord.TextChannel):
                logger.warning(
                    f"Log-Kanal {config.log_channel_id} nicht gefunden oder ist kein Text-Kanal in Guild {member.guild.id}"
                )
                return

            # Erstelle Join-Embed
            embed = discord.Embed(
                title="Mitglied beigetreten",
                description=f"{member.mention} ist dem Server beigetreten",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )

            # Member-Informationen
            embed.add_field(
                name="Benutzername",
                value=f"{member.name}",
                inline=True,
            )

            embed.add_field(name="Benutzer-ID", value=str(member.id), inline=True)

            embed.add_field(
                name="Account erstellt",
                value=f"<t:{int(member.created_at.timestamp())}:f>",
                inline=True,
            )

            # Member-Count
            member_count = member.guild.member_count

            # Avatar als Thumbnail
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)

            # Footer
            embed.set_footer(
                text=f"{member_count} Mitglieder",
                icon_url=member.display_avatar.url if member.display_avatar else None,
            )

            # Sende Log-Nachricht
            await log_channel.send(embed=embed)

            logger.info(
                f"Member Join geloggt: {member} ({member.id}) in Guild {member.guild.name} ({member.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Loggen von Member Join für {member}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Event Handler für Member Leave"""
        try:
            if not member.guild:
                return

            # Hole Server-Konfiguration
            config = await self.bot.db.get_guild_config(member.guild.id)

            # Prüfe ob Log-Kanal konfiguriert ist
            if not config.log_channel_id:
                return

            # Hole Log-Kanal
            log_channel = member.guild.get_channel(config.log_channel_id)
            if not log_channel or not isinstance(log_channel, discord.TextChannel):
                logger.warning(
                    f"Log-Kanal {config.log_channel_id} nicht gefunden oder ist kein Text-Kanal in Guild {member.guild.id}"
                )
                return

            # Prüfe Audit-Logs für Kick/Ban-Grund
            leave_reason, audit_reason = await self._get_leave_reason(member)

            # Bestimme Embed-Farbe basierend auf Grund
            if leave_reason == "kick":
                title = "Mitglied gekickt"
                description = f"{member.mention} wurde vom Server gekickt"
            elif leave_reason == "ban":
                title = "Mitglied gebannt"
                description = f"{member.mention} wurde vom Server gebannt"
            else:
                title = "Mitglied verlassen"
                description = f"{member.mention} hat den Server verlassen"

            # Erstelle Leave-Embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )

            # Member-Informationen
            embed.add_field(
                name="Benutzername",
                value=f"{member.name}",
                inline=True,
            )

            embed.add_field(name="Benutzer-ID", value=str(member.id), inline=True)

            embed.add_field(
                name="Beigetreten",
                value=f"<t:{int(member.joined_at.timestamp())}:f>"
                if member.joined_at
                else "Unbekannt",
                inline=True,
            )

            # Aufenthaltsdauer berechnen
            if member.joined_at:
                duration = datetime.now(timezone.utc) - member.joined_at
                days = duration.days
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                duration_text = []
                if days > 0:
                    duration_text.append(f"{days} Tag{'e' if days != 1 else ''}")
                if hours > 0:
                    duration_text.append(f"{hours} Stunde{'n' if hours != 1 else ''}")
                if minutes > 0:
                    duration_text.append(
                        f"{minutes} Minute{'n' if minutes != 1 else ''}"
                    )

                duration_str = (
                    ", ".join(duration_text)
                    if duration_text
                    else "Weniger als eine Minute"
                )
            else:
                duration_str = "Unbekannt"

            embed.add_field(name="Aufenthaltsdauer", value=duration_str, inline=True)

            # Füge Grund hinzu, falls verfügbar
            if audit_reason and leave_reason in ["kick", "ban"]:
                embed.add_field(name="Grund", value=audit_reason, inline=False)

            # Member-Count
            member_count = member.guild.member_count

            # Avatar als Thumbnail
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)

            # Footer
            embed.set_footer(
                text=f"{member_count} Mitglieder",
                icon_url=member.display_avatar.url if member.display_avatar else None,
            )

            # Sende Log-Nachricht
            await log_channel.send(embed=embed)

            logger.info(
                f"Member Leave geloggt: {member} ({member.id}) in Guild {member.guild.name} ({member.guild.id})"
            )

        except Exception as e:
            logger.error(f"Fehler beim Loggen von Member Leave für {member}: {e}")

    async def _get_leave_reason(
        self, member: discord.Member
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Überprüft Audit-Logs um festzustellen ob ein Member gekickt oder gebannt wurde

        Args:
            member: Das Member-Objekt das den Server verlassen hat

        Returns:
            Tuple mit ("kick", "ban" oder None für normales Verlassen, Grund aus Audit-Log oder None)
        """
        if not member.guild.me.guild_permissions.view_audit_log:
            return None, None

        try:
            # Warte kurz damit Audit-Log-Einträge verfügbar sind
            await asyncio.sleep(1)

            # Prüfe auf Kick-Einträge
            async for entry in member.guild.audit_logs(
                action=discord.AuditLogAction.kick,
                limit=5,
                after=datetime.now(timezone.utc) - timedelta(seconds=30),
            ):
                if entry.target and entry.target.id == member.id:
                    return "kick", entry.reason

            # Prüfe auf Ban-Einträge
            async for entry in member.guild.audit_logs(
                action=discord.AuditLogAction.ban,
                limit=5,
                after=datetime.now(timezone.utc) - timedelta(seconds=30),
            ):
                if entry.target and entry.target.id == member.id:
                    return "ban", entry.reason

        except discord.Forbidden:
            logger.warning(
                f"Keine Berechtigung für Audit-Logs in Guild {member.guild.id}"
            )
        except Exception as e:
            logger.error(f"Fehler beim Überprüfen der Audit-Logs für {member}: {e}")

        return None, None


async def setup(bot):
    """Lädt das Member Log Cog"""
    await bot.add_cog(MemberLogCog(bot))
    logger.info("Member Log Cog geladen")
