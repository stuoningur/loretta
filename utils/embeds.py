"""
Embed factory for consistent Discord embed creation
"""

import discord
from typing import Optional, Union


class EmbedFactory:
    """Factory class for creating consistent Discord embeds"""

    @staticmethod
    def error_embed(title: str, description: str) -> discord.Embed:
        """Create a red error embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.red()
        )

    @staticmethod
    def success_embed(title: str, description: str) -> discord.Embed:
        """Create a green success embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.green()
        )

    @staticmethod
    def info_embed(title: str, description: str) -> discord.Embed:
        """Create a blurple info embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.blurple()
        )

    @staticmethod
    def warning_embed(title: str, description: str) -> discord.Embed:
        """Create a yellow warning embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.yellow()
        )

    @staticmethod
    def specs_embed(
        user: Union[discord.Member, discord.User],
        specs_text: str,
        requester: Union[discord.Member, discord.User],
        updated_at: Optional[str] = None,
    ) -> discord.Embed:
        """Create a specifications display embed"""
        embed = discord.Embed(
            title=f"PC von: {user.display_name}",
            description=specs_text,
            color=discord.Color.blurple(),
        )

        if updated_at:
            # Parse timestamp if provided
            try:
                from datetime import datetime, timezone

                dt = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
                timestamp = int(dt.timestamp())

                embed.add_field(
                    name="Zuletzt aktualisiert",
                    value=f"<t:{timestamp}:F>",
                    inline=False,
                )
            except Exception:
                pass  # If timestamp parsing fails, just skip the field

        embed.set_footer(
            text=f"Angefordert von {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )

        return embed

    @staticmethod
    def no_specs_embed(user: Union[discord.Member, discord.User]) -> discord.Embed:
        """Create embed for when no specifications are found"""
        return EmbedFactory.error_embed(
            "Keine Spezifikationen gefunden",
            f"{user.display_name} hat keine Spezifikationen registriert.",
        )

    @staticmethod
    def database_error_embed(operation: str = "Operation") -> discord.Embed:
        """Create a database error embed"""
        return EmbedFactory.error_embed(
            "Datenbankfehler",
            f"Die {operation} konnte nicht durchgeführt werden. Bitte versuche es später erneut.",
        )

    @staticmethod
    def unexpected_error_embed(operation: str = "Operation") -> discord.Embed:
        """Create an unexpected error embed"""
        return EmbedFactory.error_embed(
            "Unerwarteter Fehler",
            f"Es ist ein unerwarteter Fehler bei der {operation} aufgetreten.",
        )

    @staticmethod
    def missing_permissions_embed(permissions: str) -> discord.Embed:
        """Create a missing permissions error embed"""
        return EmbedFactory.error_embed(
            "Fehlende Berechtigung",
            f"Du hast nicht die erforderliche Berechtigung: **{permissions}**",
        )

    @staticmethod
    def command_not_found_embed(command_name: str) -> discord.Embed:
        """Create a command not found error embed"""
        return EmbedFactory.error_embed(
            "Befehl nicht gefunden",
            f"Der Befehl `{command_name}` existiert nicht.\nVerwende `/help` für eine Liste aller verfügbaren Befehle.",
        )

    @staticmethod
    def missing_argument_embed(argument: str) -> discord.Embed:
        """Create a missing argument error embed"""
        return EmbedFactory.error_embed(
            "Fehlender Parameter",
            f"Der erforderliche Parameter `{argument}` fehlt.\nÜberprüfe die Befehlsyntax mit `/help`.",
        )

    @staticmethod
    def bad_argument_embed(argument: str, expected_type: str) -> discord.Embed:
        """Create a bad argument error embed"""
        return EmbedFactory.error_embed(
            "Ungültiger Parameter",
            f"Der Parameter `{argument}` hat einen ungültigen Wert.\nErwartet wird: **{expected_type}**",
        )

    @staticmethod
    def too_many_arguments_embed() -> discord.Embed:
        """Create a too many arguments error embed"""
        return EmbedFactory.error_embed(
            "Zu viele Parameter",
            "Du hast zu viele Parameter angegeben.\nÜberprüfe die Befehlsyntax mit `/help`.",
        )

    @staticmethod
    def cooldown_embed(retry_after: float) -> discord.Embed:
        """Create a cooldown error embed"""
        return EmbedFactory.error_embed(
            "Abklingzeit aktiv",
            f"Du musst noch {retry_after:.1f} Sekunden warten, bevor du diesen Befehl erneut verwenden kannst.",
        )

    @staticmethod
    def bot_missing_permissions_embed(permissions: str) -> discord.Embed:
        """Create a bot missing permissions error embed"""
        return EmbedFactory.error_embed(
            "Bot-Berechtigung fehlt",
            f"Mir fehlt die erforderliche Berechtigung: **{permissions}**\nBitte kontaktiere einen Administrator.",
        )

    @staticmethod
    def dm_only_embed() -> discord.Embed:
        """Create a DM only error embed"""
        return EmbedFactory.error_embed(
            "Nur in Direktnachrichten",
            "Dieser Befehl kann nur in Direktnachrichten verwendet werden.",
        )

    @staticmethod
    def guild_only_embed() -> discord.Embed:
        """Create a guild only error embed"""
        return EmbedFactory.error_embed(
            "Nur auf Servern verfügbar",
            "Dieser Befehl kann nur auf Servern verwendet werden, nicht in Direktnachrichten.",
        )
