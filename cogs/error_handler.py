import logging
import discord
from discord.ext import commands
from utils.embeds import EmbedFactory

logger = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    """Globaler Error Handler für alle Commands und App Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Globaler Error Handler für alle Commands"""
        # Verhindere Mehrfachbehandlung von Fehlern wenn Cogs eigene Handler haben
        if hasattr(ctx.command, "on_error"):
            return

        # Original Exception extrahieren falls vorhanden
        error = getattr(error, "original", error)

        # Logge den Fehler für Debugging (ohne vollständigen Traceback für bekannte Fehler)
        if isinstance(
            error,
            (
                commands.CommandNotFound,
                commands.MissingRequiredArgument,
                commands.BadArgument,
                commands.TooManyArguments,
                commands.MissingPermissions,
                commands.BotMissingPermissions,
                commands.CommandOnCooldown,
                commands.NoPrivateMessage,
                commands.PrivateMessageOnly,
                commands.DisabledCommand,
                commands.NotOwner,
                commands.CheckFailure,
                discord.HTTPException,
            ),
        ):
            # Für bekannte Fehler nur grundlegendes Logging ohne Traceback
            pass
        else:
            # Für unbekannte Fehler vollständiges Logging mit Traceback
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.error(
                f"Befehlsfehler in {ctx.command} in {guild_info}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung
        if isinstance(error, commands.CommandNotFound):
            # Extrahiere den Befehlsnamen aus der Nachricht
            prefix = await self.bot.get_prefix(ctx.message)
            if isinstance(prefix, list):
                prefix = prefix[0]  # Nimm ersten Prefix
            command_name = ctx.message.content[len(prefix) :].split()[0]
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.info(
                f"Befehl nicht gefunden: '{command_name}' von {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, commands.MissingRequiredArgument):
            param_name = getattr(getattr(error, "param", None), "name", "unbekannt")
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Fehlender erforderlicher Parameter '{param_name}' in Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.missing_argument_embed(param_name)

        elif isinstance(error, commands.BadArgument):
            # Versuche den Parameternamen und erwarteten Typ zu extrahieren
            param_name = getattr(getattr(error, "param", None), "name", "unbekannt")
            expected_type = "gültiger Wert"

            # Spezifische Typen identifizieren
            if "int" in str(error).lower():
                expected_type = "ganze Zahl"
            elif "float" in str(error).lower():
                expected_type = "Dezimalzahl"
            elif "member" in str(error).lower():
                expected_type = "Benutzername oder Erwähnung"
            elif "channel" in str(error).lower():
                expected_type = "Kanalname oder Erwähnung"
            elif "role" in str(error).lower():
                expected_type = "Rollenname oder Erwähnung"

            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Ungültiger Parameter '{param_name}' (erwartet: {expected_type}) in Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}: {str(error)}"
            )
            embed = EmbedFactory.bad_argument_embed(param_name, expected_type)

        elif isinstance(error, commands.TooManyArguments):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Zu viele Parameter für Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.too_many_arguments_embed()

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Fehlende Berechtigungen ({missing_perms}) für Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.error(
                f"Bot fehlen Berechtigungen ({missing_perms}) für Befehl {ctx.command} in {ctx.guild.name if ctx.guild else 'DM'} (Guild ID: {ctx.guild.id if ctx.guild else 'N/A'})"
            )
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.CommandOnCooldown):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.info(
                f"Befehl {ctx.command} auf Abklingzeit für {ctx.author} ({ctx.author.id}) in {guild_info}, Wiederholen nach {error.retry_after:.1f}s"
            )
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, commands.NoPrivateMessage):
            logger.warning(
                f"Nur-Guild-Befehl {ctx.command} in DM versucht von {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, commands.PrivateMessageOnly):
            guild_info = (
                f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "unbekannt"
            )
            logger.warning(
                f"Nur-DM-Befehl {ctx.command} in Guild {guild_info} versucht von {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.dm_only_embed()

        elif isinstance(error, commands.DisabledCommand):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.info(
                f"Deaktivierter Befehl {ctx.command} versucht von {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.error_embed(
                "Befehl deaktiviert", "Dieser Befehl ist derzeit deaktiviert."
            )

        elif isinstance(error, commands.NotOwner):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Nur-Owner-Befehl {ctx.command} versucht von Nicht-Owner {ctx.author} ({ctx.author.id}) in {guild_info}"
            )
            embed = EmbedFactory.error_embed(
                "Berechtigung verweigert",
                "Nur der Bot-Besitzer kann diesen Befehl verwenden.",
            )

        elif isinstance(error, commands.CheckFailure):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.warning(
                f"Überprüfung fehlgeschlagen für Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}: {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Überprüfung fehlgeschlagen",
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl.",
            )

        elif isinstance(error, discord.HTTPException):
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.error(
                f"HTTP-Ausnahme in Befehl {ctx.command} von {ctx.author} ({ctx.author.id}) in {guild_info}: {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Befehlsausführung")
            guild_info = f"{ctx.guild.name} (ID: {ctx.guild.id})" if ctx.guild else "DM"
            logger.error(
                f"Unbehandelter Fehler in {guild_info}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        # Sende Error-Embed
        if embed:
            try:
                # Versuche ephemeral für Slash Commands
                if ctx.interaction and not ctx.interaction.response.is_done():
                    await ctx.interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
                elif ctx.interaction and ctx.interaction.response.is_done():
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.send(embed=embed)
            except Exception as send_error:
                logger.error(f"Fehler beim Senden der Fehlermeldung: {send_error}")

    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        """Globaler Error Handler für Slash Commands"""
        # Logge den Fehler für Debugging (ohne vollständigen Traceback für bekannte Fehler)
        if isinstance(
            error,
            (
                discord.app_commands.CommandNotFound,
                discord.app_commands.MissingPermissions,
                discord.app_commands.BotMissingPermissions,
                discord.app_commands.CommandOnCooldown,
                discord.app_commands.NoPrivateMessage,
                discord.app_commands.CheckFailure,
                discord.HTTPException,
            ),
        ):
            # Für bekannte Fehler nur grundlegendes Logging ohne Traceback
            pass
        else:
            # Für unbekannte Fehler vollständiges Logging mit Traceback
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.error(
                f"App-Command-Fehler in {interaction.command} in {guild_info}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung für App Commands
        if isinstance(error, discord.app_commands.CommandNotFound):
            command_name = "unbekannt"
            if interaction.data and "name" in interaction.data:
                command_name = interaction.data["name"]
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.info(
                f"App-Command nicht gefunden: '{command_name}' von {interaction.user} ({interaction.user.id}) in {guild_info}"
            )
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, discord.app_commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.warning(
                f"Fehlende Berechtigungen ({missing_perms}) für App-Command {interaction.command} von {interaction.user} ({interaction.user.id}) in {guild_info}"
            )
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.error(
                f"Bot fehlen Berechtigungen ({missing_perms}) für App-Command {interaction.command} in {interaction.guild.name if interaction.guild else 'DM'} (Guild ID: {interaction.guild.id if interaction.guild else 'N/A'})"
            )
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.info(
                f"App-Command {interaction.command} auf Abklingzeit für {interaction.user} ({interaction.user.id}) in {guild_info}, Wiederholen nach {error.retry_after:.1f}s"
            )
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, discord.app_commands.NoPrivateMessage):
            logger.warning(
                f"Nur-Guild-App-Command {interaction.command} in DM versucht von {interaction.user} ({interaction.user.id})"
            )
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, discord.app_commands.CheckFailure):
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.warning(
                f"Überprüfung fehlgeschlagen für App-Command {interaction.command} von {interaction.user} ({interaction.user.id}) in {guild_info}: {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Überprüfung fehlgeschlagen",
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl.",
            )

        elif isinstance(error, discord.HTTPException):
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.error(
                f"HTTP-Ausnahme in App-Command {interaction.command} von {interaction.user} ({interaction.user.id}) in {guild_info}: {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Slash-Befehlsausführung")
            guild_info = (
                f"{interaction.guild.name} (ID: {interaction.guild.id})"
                if interaction.guild
                else "DM"
            )
            logger.error(
                f"Unbehandelter App-Command-Fehler in {guild_info}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        # Sende Error-Embed
        if embed:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as send_error:
                logger.error(
                    f"Fehler beim Senden der App Command Fehlermeldung: {send_error}"
                )


async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ErrorHandler(bot))
