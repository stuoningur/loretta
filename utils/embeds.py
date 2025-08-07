"""
Embed-Factory für konsistente Discord-Embed-Erstellung
"""

import discord
from typing import Optional, Union


class EmbedFactory:
    """Factory-Klasse für die Erstellung konsistenter Discord-Embeds"""

    @staticmethod
    def error_embed(title: str, description: str) -> discord.Embed:
        """Erstellt ein rotes Fehler-Embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.red()
        )

    @staticmethod
    def success_embed(title: str, description: str) -> discord.Embed:
        """Erstellt ein grünes Erfolgs-Embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.green()
        )

    @staticmethod
    def info_embed(title: str, description: str) -> discord.Embed:
        """Erstellt ein blurples Info-Embed"""
        return discord.Embed(
            title=title, description=description, color=discord.Color.blurple()
        )

    @staticmethod
    def warning_embed(title: str, description: str) -> discord.Embed:
        """Erstellt ein gelbes Warn-Embed"""
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
        """Erstellt ein Spezifikations-Anzeige-Embed"""
        embed = discord.Embed(
            title=f"PC von: {user.display_name}",
            description=specs_text,
            color=discord.Color.blurple(),
        )

        if updated_at:
            # Parse Zeitstempel falls bereitgestellt
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
                pass  # Falls Zeitstempel-Parsing fehlschlägt, überspringe das Feld

        embed.set_footer(
            text=f"Angefordert von {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )

        return embed

    @staticmethod
    def no_specs_embed(user: Union[discord.Member, discord.User]) -> discord.Embed:
        """Erstellt Embed wenn keine Spezifikationen gefunden wurden"""
        return EmbedFactory.error_embed(
            "Keine Spezifikationen gefunden",
            f"{user.display_name} hat keine Spezifikationen registriert.",
        )

    @staticmethod
    def database_error_embed(operation: str = "Operation") -> discord.Embed:
        """Erstellt ein Datenbank-Fehler-Embed"""
        return EmbedFactory.error_embed(
            "Datenbankfehler",
            f"Die {operation} konnte nicht durchgeführt werden. Bitte versuche es später erneut.",
        )

    @staticmethod
    def unexpected_error_embed(operation: str = "Operation") -> discord.Embed:
        """Erstellt ein unerwartetes Fehler-Embed"""
        return EmbedFactory.error_embed(
            "Unerwarteter Fehler",
            f"Es ist ein unerwarteter Fehler bei der {operation} aufgetreten.",
        )

    @staticmethod
    def missing_permissions_embed(permissions: str) -> discord.Embed:
        """Erstellt ein Embed für fehlende Berechtigungen"""
        return EmbedFactory.error_embed(
            "Fehlende Berechtigung",
            f"Du hast nicht die erforderliche Berechtigung: **{permissions}**",
        )

    @staticmethod
    def command_not_found_embed(command_name: str) -> discord.Embed:
        """Erstellt ein Embed für nicht gefundenen Befehl"""
        return EmbedFactory.error_embed(
            "Befehl nicht gefunden",
            f"Der Befehl `{command_name}` existiert nicht.\nVerwende `/help` für eine Liste aller verfügbaren Befehle.",
        )

    @staticmethod
    def missing_argument_embed(argument: str) -> discord.Embed:
        """Erstellt ein Embed für fehlende Argumente"""
        return EmbedFactory.error_embed(
            "Fehlender Parameter",
            f"Der erforderliche Parameter `{argument}` fehlt.\nÜberprüfe die Befehlsyntax mit `/help`.",
        )

    @staticmethod
    def bad_argument_embed(argument: str, expected_type: str) -> discord.Embed:
        """Erstellt ein Embed für ungültige Argumente"""
        return EmbedFactory.error_embed(
            "Ungültiger Parameter",
            f"Der Parameter `{argument}` hat einen ungültigen Wert.\nErwartet wird: **{expected_type}**",
        )

    @staticmethod
    def too_many_arguments_embed() -> discord.Embed:
        """Erstellt ein Embed für zu viele Argumente"""
        return EmbedFactory.error_embed(
            "Zu viele Parameter",
            "Du hast zu viele Parameter angegeben.\nÜberprüfe die Befehlsyntax mit `/help`.",
        )

    @staticmethod
    def cooldown_embed(retry_after: float) -> discord.Embed:
        """Erstellt ein Abklingzeit-Fehler-Embed"""
        return EmbedFactory.error_embed(
            "Abklingzeit aktiv",
            f"Du musst noch {retry_after:.1f} Sekunden warten, bevor du diesen Befehl erneut verwenden kannst.",
        )

    @staticmethod
    def bot_missing_permissions_embed(permissions: str) -> discord.Embed:
        """Erstellt ein Embed für fehlende Bot-Berechtigungen"""
        return EmbedFactory.error_embed(
            "Bot-Berechtigung fehlt",
            f"Mir fehlt die erforderliche Berechtigung: **{permissions}**\nBitte kontaktiere einen Administrator.",
        )

    @staticmethod
    def dm_only_embed() -> discord.Embed:
        """Erstellt ein Embed für Nur-DM-Fehler"""
        return EmbedFactory.error_embed(
            "Nur in Direktnachrichten",
            "Dieser Befehl kann nur in Direktnachrichten verwendet werden.",
        )

    @staticmethod
    def guild_only_embed() -> discord.Embed:
        """Erstellt ein Embed für Nur-Guild-Fehler"""
        return EmbedFactory.error_embed(
            "Nur auf Servern verfügbar",
            "Dieser Befehl kann nur auf Servern verwendet werden, nicht in Direktnachrichten.",
        )
