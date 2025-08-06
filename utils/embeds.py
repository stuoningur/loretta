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
