import logging

import discord
from discord.ext import commands

from bot.utils.embeds import EmbedFactory
from bot.utils.responses import send_response
from utils.formatting import format_command_context

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
            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                error_type=type(error).__name__,
                error=str(error),
            )
            logger.error(
                f"Befehlsfehler - {context_info}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung
        if isinstance(error, commands.CommandNotFound):
            # Extrahiere den Befehlsnamen aus der Nachricht
            prefix = await self.bot.get_prefix(ctx.message)
            if isinstance(prefix, list):
                prefix = prefix[0]  # Nimm ersten Prefix

            # Prüfe ob es sich um mehrfache Prefixes handelt (z.B. !!!!, ????)
            content_after_prefix = ctx.message.content[len(prefix) :]

            # Wenn nach dem Prefix nur weitere Prefixe kommen, ignoriere es
            if all(char == prefix for char in content_after_prefix.strip()):
                return  # Ignoriere mehrfache Prefixes ohne Fehlermeldung

            command_name = (
                content_after_prefix.split()[0] if content_after_prefix.strip() else ""
            )

            # Wenn der "Befehl" nur aus Prefix-Zeichen besteht, ignoriere es
            if not command_name or all(char == prefix for char in command_name):
                return

            context_info = format_command_context(
                command_name, ctx.author, ctx.guild, status="nicht gefunden"
            )
            logger.info(f"Befehl nicht gefunden - {context_info}")
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, commands.MissingRequiredArgument):
            param_name = getattr(getattr(error, "param", None), "name", "unbekannt")
            context_info = format_command_context(
                str(ctx.command), ctx.author, ctx.guild, missing_param=param_name
            )
            logger.warning(f"Fehlender erforderlicher Parameter - {context_info}")
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

            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                invalid_param=param_name,
                expected_type=expected_type,
                error=str(error),
            )
            logger.warning(f"Ungültiger Parameter - {context_info}")
            embed = EmbedFactory.bad_argument_embed(param_name, expected_type)

        elif isinstance(error, commands.TooManyArguments):
            context_info = format_command_context(
                str(ctx.command), ctx.author, ctx.guild, issue="zu_viele_parameter"
            )
            logger.warning(f"Zu viele Parameter - {context_info}")
            embed = EmbedFactory.too_many_arguments_embed()

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                missing_permissions=missing_perms,
            )
            logger.warning(f"Fehlende Berechtigungen - {context_info}")
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                bot_missing_permissions=missing_perms,
            )
            logger.error(f"Bot fehlen Berechtigungen - {context_info}")
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.CommandOnCooldown):
            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                cooldown_retry_after=f"{error.retry_after:.1f}s",
            )
            logger.info(f"Befehl auf Abklingzeit - {context_info}")
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, commands.NoPrivateMessage):
            context_info = format_command_context(
                str(ctx.command), ctx.author, None, issue="nur_guild_befehl_in_dm"
            )
            logger.warning(f"Nur-Guild-Befehl in DM versucht - {context_info}")
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, commands.PrivateMessageOnly):
            context_info = format_command_context(
                str(ctx.command), ctx.author, ctx.guild, issue="nur_dm_befehl_in_guild"
            )
            logger.warning(f"Nur-DM-Befehl in Guild versucht - {context_info}")
            embed = EmbedFactory.dm_only_embed()

        elif isinstance(error, commands.DisabledCommand):
            context_info = format_command_context(
                str(ctx.command), ctx.author, ctx.guild, issue="befehl_deaktiviert"
            )
            logger.info(f"Deaktivierter Befehl versucht - {context_info}")
            embed = EmbedFactory.error_embed(
                "Befehl deaktiviert", "Dieser Befehl ist derzeit deaktiviert."
            )

        elif isinstance(error, commands.NotOwner):
            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                issue="nur_owner_befehl_von_nicht_owner",
            )
            logger.warning(
                f"Nur-Owner-Befehl von Nicht-Owner versucht - {context_info}"
            )
            embed = EmbedFactory.error_embed(
                "Berechtigung verweigert",
                "Nur der Bot-Besitzer kann diesen Befehl verwenden.",
            )

        elif isinstance(error, commands.CheckFailure):
            # Erweitere die Fehlermeldung basierend auf dem Befehl und Kontext
            check_type = "unbekannt"
            detailed_message = (
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl."
            )

            # Spezifische Check-Typen identifizieren
            error_msg = str(error).lower()
            if "owner" in error_msg or "is_owner" in error_msg:
                check_type = "owner_check"
                detailed_message = "Nur der Bot-Besitzer kann diesen Befehl verwenden."
            elif "permission" in error_msg:
                check_type = "permission_check"
                detailed_message = (
                    "Du hast nicht die erforderlichen Berechtigungen für diesen Befehl."
                )
            elif "guild" in error_msg and "only" in error_msg:
                check_type = "guild_only_check"
                detailed_message = (
                    "Dieser Befehl kann nur auf einem Server verwendet werden."
                )
            elif "dm" in error_msg and "only" in error_msg:
                check_type = "dm_only_check"
                detailed_message = (
                    "Dieser Befehl kann nur in Direktnachrichten verwendet werden."
                )
            elif "cooldown" in error_msg:
                check_type = "cooldown_check"
                detailed_message = (
                    "Du musst warten, bevor du diesen Befehl erneut verwenden kannst."
                )

            context_info = format_command_context(
                str(ctx.command),
                ctx.author,
                ctx.guild,
                check_failure=str(error),
                check_type=check_type,
            )
            logger.warning(
                f"Überprüfung fehlgeschlagen ({check_type}) - {context_info}"
            )
            embed = EmbedFactory.error_embed(
                "Berechtigung verweigert",
                detailed_message,
            )

        elif isinstance(error, discord.HTTPException):
            context_info = format_command_context(
                str(ctx.command), ctx.author, ctx.guild, http_exception=str(error)
            )
            logger.error(f"HTTP-Ausnahme - {context_info}")
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Befehlsausführung")
            context_info = format_command_context(
                "unbekannt",
                ctx.author,
                ctx.guild,
                error_type=type(error).__name__,
                error=str(error),
            )
            logger.error(
                f"Unbehandelter Fehler - {context_info}",
                exc_info=error,
            )

        # Sende Error-Embed
        if embed:
            try:
                await send_response(ctx, embed, ephemeral=True)
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
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                error_type=type(error).__name__,
                error=str(error),
            )
            logger.error(
                f"App-Command-Fehler - {context_info}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung für App Commands
        if isinstance(error, discord.app_commands.CommandNotFound):
            command_name = "unbekannt"
            if interaction.data and "name" in interaction.data:
                command_name = interaction.data["name"]
            context_info = format_command_context(
                command_name,
                interaction.user,
                interaction.guild,
                status="nicht_gefunden",
            )
            logger.info(f"App-Command nicht gefunden - {context_info}")
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, discord.app_commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                missing_permissions=missing_perms,
            )
            logger.warning(f"Fehlende Berechtigungen (App-Command) - {context_info}")
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                bot_missing_permissions=missing_perms,
            )
            logger.error(f"Bot fehlen Berechtigungen (App-Command) - {context_info}")
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                cooldown_retry_after=f"{error.retry_after:.1f}s",
            )
            logger.info(f"App-Command auf Abklingzeit - {context_info}")
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, discord.app_commands.NoPrivateMessage):
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                None,
                issue="nur_guild_app_command_in_dm",
            )
            logger.warning(f"Nur-Guild-App-Command in DM versucht - {context_info}")
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, discord.app_commands.CheckFailure):
            # Erweitere die Fehlermeldung basierend auf dem Befehl und Kontext
            check_type = "unbekannt"
            detailed_message = (
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl."
            )

            # Spezifische Check-Typen identifizieren
            error_msg = str(error).lower()
            if "owner" in error_msg or "is_owner" in error_msg:
                check_type = "owner_check"
                detailed_message = "Nur der Bot-Besitzer kann diesen Befehl verwenden."
            elif "permission" in error_msg:
                check_type = "permission_check"
                detailed_message = (
                    "Du hast nicht die erforderlichen Berechtigungen für diesen Befehl."
                )
            elif "guild" in error_msg and "only" in error_msg:
                check_type = "guild_only_check"
                detailed_message = (
                    "Dieser Befehl kann nur auf einem Server verwendet werden."
                )
            elif "dm" in error_msg and "only" in error_msg:
                check_type = "dm_only_check"
                detailed_message = (
                    "Dieser Befehl kann nur in Direktnachrichten verwendet werden."
                )
            elif "cooldown" in error_msg:
                check_type = "cooldown_check"
                detailed_message = (
                    "Du musst warten, bevor du diesen Befehl erneut verwenden kannst."
                )

            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                check_failure=str(error),
                check_type=check_type,
            )
            logger.warning(
                f"Überprüfung fehlgeschlagen ({check_type}) (App-Command) - {context_info}"
            )
            embed = EmbedFactory.error_embed(
                "Berechtigung verweigert",
                detailed_message,
            )

        elif isinstance(error, discord.HTTPException):
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                http_exception=str(error),
            )
            logger.error(f"HTTP-Ausnahme (App-Command) - {context_info}")
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Slash-Befehlsausführung")
            context_info = format_command_context(
                str(interaction.command),
                interaction.user,
                interaction.guild,
                error_type=type(error).__name__,
                error=str(error),
            )
            logger.error(
                f"Unbehandelter App-Command-Fehler - {context_info}",
                exc_info=error,
            )

        # Sende Error-Embed
        if embed:
            try:
                await send_response(interaction, embed, ephemeral=True)
            except Exception as send_error:
                logger.error(
                    f"Fehler beim Senden der App Command Fehlermeldung: {send_error}"
                )


async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ErrorHandler(bot))
