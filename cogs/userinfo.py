"""
Userinfo Befehle für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UserInfo(commands.Cog):
    """Userinfo Befehle und Funktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Zeigt Informationen über einen Benutzer an",
    )
    async def userinfo(self, ctx, *, user: Optional[str] = None):
        """Zeigt detaillierte Informationen über einen Benutzer an"""
        # Wenn kein User angegeben wurde, verwende den Autor des Befehls
        if user is None:
            target_user = ctx.author
        else:
            # Versuche den User zu konvertieren
            try:
                converter = commands.MemberConverter()
                target_user = await converter.convert(ctx, user)
            except commands.MemberNotFound:
                await ctx.send("Benutzer nicht gefunden. Bitte überprüfe die Eingabe.")
                logger.warning(
                    f"Userinfo-Befehl: Benutzer nicht gefunden - {ctx.author}"
                )
                return

        # Hole das Member-Objekt neu vom Server für aktuelle Daten
        if isinstance(target_user, discord.Member) and ctx.guild:
            fresh_member = ctx.guild.get_member(target_user.id)
            if fresh_member:
                logger.info(f"Verwende frisches Member-Objekt für {target_user.name}")
                target_user = fresh_member
            else:
                logger.error(
                    f"Konnte kein frisches Member-Objekt für {target_user.name} finden, verwende vorhandenes"
                )

        # Erstelle Embed mit der Helper-Methode
        embed = await self.create_userinfo_embed(target_user, ctx.author)

        try:
            await ctx.send(embed=embed)
            logger.info(
                f"Userinfo-Befehl ausgeführt von {ctx.author} für Benutzer {target_user.name}"
            )
        except discord.HTTPException as e:
            logger.error(f"Fehler beim Senden der Userinfo: {e}")
            await ctx.send("Fehler beim Anzeigen der Benutzerinformationen.")

    async def create_userinfo_embed(self, user, requester):
        """Erstellt ein Userinfo-Embed für die gegebenen Benutzer"""
        embed = discord.Embed(
            title="Benutzer Informationen",
            color=user.color
            if user.color != discord.Color.default()
            else discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Benutzer-Avatar hinzufügen
        embed.set_thumbnail(url=user.display_avatar.url)

        # Grundinformationen
        embed.add_field(
            name="Allgemeine Informationen",
            value=f"**Name:** {user.display_name}\n"
            f"**Benutzername:** {user.name}\n"
            f"**ID:** {user.id}\n"
            f"**Bot:** {'Ja' if user.bot else 'Nein'}",
            inline=False,
        )

        # Account-Informationen
        created_at = user.created_at
        joined_at = (
            user.joined_at if hasattr(user, "joined_at") and user.joined_at else None
        )

        account_info = f"**Account erstellt:** <t:{int(created_at.timestamp())}:R>\n"
        if joined_at:
            account_info += (
                f"**Server beigetreten:** <t:{int(joined_at.timestamp())}:R>"
            )

        embed.add_field(
            name="Account Informationen",
            value=account_info,
            inline=False,
        )

        # Server-spezifische Informationen
        if isinstance(user, discord.Member):
            # Status und Aktivität
            status_text = {
                discord.Status.online: "Online",
                discord.Status.idle: "Abwesend",
                discord.Status.dnd: "Bitte nicht stören",
                discord.Status.offline: "Offline",
            }

            # Hol den Status vom status_text
            status_info = f"**Status:** {status_text.get(user.status, 'Unbekannt')}"

            # Aktivität hinzufügen falls vorhanden (Custom Activities überspringen)
            if user.activities:
                for activity in user.activities:
                    # Custom Activities überspringen
                    if isinstance(activity, discord.CustomActivity):
                        continue

                    if isinstance(activity, discord.Game):
                        status_info += f"\n**Spielt:** {activity.name}"
                        break
                    elif isinstance(activity, discord.Streaming):
                        status_info += f"\n**Streamt:** {activity.name}"
                        break
                    elif isinstance(activity, discord.Activity):
                        status_info += f"\n**Aktivität:** {activity.name}"
                        break

            embed.add_field(
                name="Status & Aktivität",
                value=status_info,
                inline=True,
            )

            # Rollen (außer @everyone)
            roles = [
                role.mention for role in user.roles[1:]
            ]  # Erste Rolle ist @everyone
            if roles:
                roles_text = ", ".join(roles[:10])  # Maximal 10 Rollen anzeigen
                if len(user.roles) > 11:  # 10 + @everyone
                    roles_text += f" ... und {len(user.roles) - 11} weitere"
            else:
                roles_text = "Keine Rollen"

            embed.add_field(
                name=f"Rollen ({len(user.roles) - 1})",
                value=roles_text,
                inline=False,
            )

            # Berechtigung Informationen
            key_permissions = []
            if user.guild_permissions.administrator:
                key_permissions.append("Administrator")
            if user.guild_permissions.manage_guild:
                key_permissions.append("Server verwalten")
            if user.guild_permissions.manage_channels:
                key_permissions.append("Kanäle verwalten")
            if user.guild_permissions.manage_messages:
                key_permissions.append("Nachrichten verwalten")
            if user.guild_permissions.kick_members:
                key_permissions.append("Mitglieder kicken")
            if user.guild_permissions.ban_members:
                key_permissions.append("Mitglieder bannen")

            if key_permissions:
                embed.add_field(
                    name="Wichtige Berechtigungen",
                    value=", ".join(key_permissions),
                    inline=False,
                )

        # Footer
        embed.set_footer(
            text=f"Angefordert von {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )

        return embed


@discord.app_commands.context_menu(name="Benutzerinfo")
async def userinfo_context_menu(interaction: discord.Interaction, user: discord.Member):
    """Context Menu für Benutzerinformationen"""
    # Hole das UserInfo Cog um die Helper-Methode zu verwenden
    userinfo_cog = interaction.client.get_cog("UserInfo")  # type: ignore
    if not userinfo_cog:
        await interaction.response.send_message(
            "Userinfo-System ist nicht verfügbar.", ephemeral=True
        )
        return

    try:
        # Hole das Member-Objekt neu vom Server für aktuelle Presence-Daten
        if interaction.guild:
            fresh_member = interaction.guild.get_member(user.id)
            if fresh_member:
                logger.info(
                    f"Kontextmenü: Verwende frisches Member-Objekt für {user.name}"
                )
                user = fresh_member
            else:
                logger.error(
                    f"Kontextmenü: Konnte kein frisches Member-Objekt für {user.name} finden, verwende vorhandenes"
                )

        embed = await userinfo_cog.create_userinfo_embed(user, interaction.user)
        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Userinfo-Kontextmenü verwendet von {interaction.user} für Benutzer {user.name}"
        )
    except discord.HTTPException as e:
        logger.error(f"Fehler beim Senden der Userinfo über Kontextmenü: {e}")
        await interaction.response.send_message(
            "Fehler beim Anzeigen der Benutzerinformationen.", ephemeral=True
        )


async def setup(bot):
    """Lädt das UserInfo Cog"""
    await bot.add_cog(UserInfo(bot))

    # Füge das Context Menu hinzu
    bot.tree.add_command(userinfo_context_menu)

    logger.info("UserInfo-Cog und Kontextmenü geladen")
