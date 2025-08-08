"""
Utility-Funktionen für konsistente Formatierung
"""

import discord
from typing import Optional, Union


def format_guild_info(guild: Optional[discord.Guild]) -> str:
    """
    Formatiert Guild-Informationen konsistent

    Args:
        guild: Guild-Objekt oder None für DMs

    Returns:
        Formatierter Guild-Info-String
    """
    return f"{guild.name} (ID: {guild.id})" if guild else "DM"


def format_user_info(user: Union[discord.Member, discord.User]) -> str:
    """
    Formatiert Benutzer-Informationen konsistent
    Format: DisplayName (ID)

    Args:
        user: Member oder User-Objekt

    Returns:
        Formatierter Benutzer-Info-String
    """
    display_name = user.display_name if hasattr(user, "display_name") else user.name
    return f"{display_name} ({user.id})"


def format_channel_info(channel: Optional[discord.abc.GuildChannel]) -> str:
    """
    Formatiert Kanal-Informationen konsistent

    Args:
        channel: Kanal-Objekt oder None

    Returns:
        Formatierter Kanal-Info-String
    """
    if not channel:
        return "Unbekannter Kanal"

    return f"#{channel.name}" if hasattr(channel, "name") else str(channel)


def format_command_context(
    command_name: str,
    user: Union[discord.Member, discord.User],
    guild: Optional[discord.Guild],
    **kwargs,
) -> str:
    """
    Formatiert Command-Context für Logging
    Format: Guild Name (ID) - User DisplayName (ID) - Command run - additional details

    Args:
        command_name: Name des Commands
        user: Benutzer der den Command ausführt
        guild: Guild wo der Command ausgeführt wird
        **kwargs: Zusätzliche Informationen für das Log

    Returns:
        Formatierter Context-String für Logging
    """
    # Guild Name (ID)
    guild_info = format_guild_info(guild)

    # User DisplayName (ID)
    user_display_name = (
        user.display_name if hasattr(user, "display_name") else user.name
    )
    user_info = f"{user_display_name} ({user.id})"

    # Command run
    command_info = f"Command '{command_name}' run"

    # Base format: Guild Name (ID) - User DisplayName (ID) - Command run
    base_info = f"{guild_info} - {user_info} - {command_info}"

    # Additional details
    if kwargs:
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        return f"{base_info} - {extra_info}"

    return base_info


def format_permission_list(permissions: list) -> str:
    """
    Formatiert eine Liste von Berechtigungen für Anzeige

    Args:
        permissions: Liste von Berechtigungs-Namen

    Returns:
        Formatierter String mit Berechtigungen
    """
    if not permissions:
        return "Keine"

    return ", ".join(permissions)


def format_member_status(status: discord.Status) -> str:
    """
    Konvertiert Discord-Status zu deutschem Text

    Args:
        status: Discord Status-Enum

    Returns:
        Deutsche Status-Beschreibung
    """
    status_map = {
        discord.Status.online: "Online",
        discord.Status.idle: "Abwesend",
        discord.Status.dnd: "Bitte nicht stören",
        discord.Status.offline: "Offline",
        discord.Status.invisible: "Unsichtbar",
    }

    return status_map.get(status, "Unbekannt")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Kürzt Text auf maximale Länge

    Args:
        text: Zu kürzender Text
        max_length: Maximale Länge
        suffix: Suffix für gekürzte Texte

    Returns:
        Gekürzter Text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_timestamp(timestamp: Optional[str], format_type: str = "F") -> str:
    """
    Formatiert Zeitstempel für Discord

    Args:
        timestamp: Zeitstempel-String oder None
        format_type: Discord-Zeitformat (F, R, D, etc.)

    Returns:
        Formatierter Discord-Zeitstempel oder Fallback
    """
    if not timestamp:
        return "Unbekannt"

    try:
        from datetime import datetime

        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        unix_timestamp = int(dt.timestamp())
        return f"<t:{unix_timestamp}:{format_type}>"
    except Exception:
        return timestamp  # Fallback zum ursprünglichen String


def format_file_size(size_bytes: int) -> str:
    """
    Formatiert Dateigröße für menschenlesbare Anzeige

    Args:
        size_bytes: Größe in Bytes

    Returns:
        Formatierte Dateigröße
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = size_bytes

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1

    return f"{size:.1f}{size_names[i]}"
