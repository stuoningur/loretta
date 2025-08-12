"""
Embed-Factory für konsistente Discord-Embed-Erstellung
"""

import re
from datetime import datetime, timezone
from typing import Optional, Union

import discord


class EmbedFactory:
    """Factory-Klasse für die Erstellung konsistenter Discord-Embeds"""

    # RSS-spezifische Konfigurationen
    RSS_COLORS = {
        "hardwareluxx": discord.Color.red(),
        "computerbase": discord.Color.blue(),
        "pcgh": discord.Color.dark_blue(),
        "software": discord.Color.blurple(),
    }

    RSS_FOOTER_CONFIG = {
        "hardwareluxx": {
            "text": "Hardwareluxx • Nachrichten",
            "icon_url": "https://github.com/stuoningur/loretta/blob/master/resources/icons/rss/hardwareluxx.png?raw=true",
        },
        "computerbase": {
            "text": "ComputerBase • Nachrichten",
            "icon_url": "https://github.com/stuoningur/loretta/blob/master/resources/icons/rss/computerbase.png?raw=true",
        },
        "pcgh": {
            "text": "PC Games Hardware • Nachrichten",
            "icon_url": "https://github.com/stuoningur/loretta/blob/master/resources/icons/rss/pcgh.png?raw=true",
        },
        "software": {
            "text": "ComputerBase • Downloads",
            "icon_url": "https://github.com/stuoningur/loretta/blob/master/resources/icons/rss/computerbase.png?raw=true",
        },
    }

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

    @staticmethod
    def command_response_embed(
        title: str,
        description: str,
        color: discord.Color,
        requester: Union[discord.Member, discord.User],
        thumbnail_url: Optional[str] = None,
    ) -> discord.Embed:
        """Erstellt ein standardmäßiges Command-Response-Embed mit Footer und Timestamp"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        embed.set_footer(
            text=f"Angefordert von {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )

        return embed

    @staticmethod
    def info_command_embed(
        title: str,
        description: str,
        requester: Union[discord.Member, discord.User],
        thumbnail_url: Optional[str] = None,
    ) -> discord.Embed:
        """Erstellt ein Info-Command-Embed mit Footer und Timestamp"""
        return EmbedFactory.command_response_embed(
            title, description, discord.Color.blurple(), requester, thumbnail_url
        )

    @staticmethod
    def success_command_embed(
        title: str,
        description: str,
        requester: Union[discord.Member, discord.User],
        thumbnail_url: Optional[str] = None,
    ) -> discord.Embed:
        """Erstellt ein Erfolgs-Command-Embed mit Footer und Timestamp"""
        return EmbedFactory.command_response_embed(
            title, description, discord.Color.green(), requester, thumbnail_url
        )

    @staticmethod
    def error_command_embed(
        title: str,
        description: str,
        requester: Union[discord.Member, discord.User],
        thumbnail_url: Optional[str] = None,
    ) -> discord.Embed:
        """Erstellt ein Fehler-Command-Embed mit Footer und Timestamp"""
        return EmbedFactory.command_response_embed(
            title, description, discord.Color.red(), requester, thumbnail_url
        )

    @staticmethod
    def single_birthday_embed(
        member: Union[discord.Member, discord.User], message: str
    ) -> discord.Embed:
        """Erstellt ein Embed für einen einzelnen Geburtstag"""
        embed = discord.Embed(
            title="🎉 Geburtstag! 🎂",
            description=message,
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="🎈 Hab einen wunderschönen Tag! 🎈")
        return embed

    @staticmethod
    def multiple_birthdays_embed(user_mentions: list) -> discord.Embed:
        """Erstellt ein Embed für mehrere Geburtstage"""
        embed = discord.Embed(
            title="🎉 Mehrere Geburtstage heute! 🎂",
            description="🎈 Herzlichen Glückwunsch an:\n" + "\n".join(user_mentions),
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="🎉 Feiert schön zusammen! 🎉")
        return embed

    @staticmethod
    def _extract_image_url(html_content: str) -> str | None:
        """
        Extrahiert die erste Bild-URL aus HTML-Content

        Args:
            html_content: HTML-String mit potentiellen Image-Tags

        Returns:
            URL des ersten gefundenen Bildes oder None
        """
        if not html_content:
            return None

        # Suche nach <img src="..."> Tags
        img_match = re.search(
            r'<img\s+[^>]*src=["\']([^"\']+)["\']', html_content, re.IGNORECASE
        )
        if img_match:
            return img_match.group(1)
        return None

    @staticmethod
    def _extract_enclosure_image(entry) -> str | None:
        """
        Extrahiert Bild-URL aus RSS-Enclosures

        Args:
            entry: RSS-Feed-Entry-Objekt

        Returns:
            URL des ersten gefundenen Bildes oder None
        """
        if not hasattr(entry, "enclosures") or not entry.enclosures:
            return None

        for enclosure in entry.enclosures:
            if (
                hasattr(enclosure, "type")
                and enclosure.type
                and enclosure.type.startswith("image/")
                and hasattr(enclosure, "url")
                and enclosure.url
            ):
                return enclosure.url
        return None

    @staticmethod
    def _clean_html_text(html_text: str, max_length: int = 200) -> str:
        """
        Entfernt HTML-Tags und kürzt Text

        Args:
            html_text: Text mit HTML-Tags
            max_length: Maximale Länge des Textes

        Returns:
            Bereinigter und gekürzter Text
        """
        # HTML-Tags entfernen
        clean_text = re.sub(r"<[^>]+>", "", html_text)

        # Text kürzen falls nötig
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."

        return clean_text.strip()

    @classmethod
    def rss_news_embed(
        cls,
        entry,
        source: str,
        include_description: bool = True,
        include_thumbnail: bool = True,
        include_category: bool = False,
        max_description_length: int = 200,
    ) -> discord.Embed:
        """
        Erstellt ein standardisiertes Embed für RSS-News

        Args:
            entry: RSS-Feed-Entry-Objekt mit title, link, summary etc.
            source: Quelle (hardwareluxx, computerbase, pcgh, software)
            include_description: Ob Beschreibung hinzugefügt werden soll
            include_thumbnail: Ob Thumbnail extrahiert werden soll
            include_category: Ob Kategorie-Feld hinzugefügt werden soll
            max_description_length: Maximale Länge der Beschreibung

        Returns:
            Fertig konfiguriertes Discord-Embed
        """
        # Grundlegendes Embed erstellen
        embed = discord.Embed(
            title=entry.title,
            url=entry.link,
            color=cls.RSS_COLORS.get(source, discord.Color.blurple()),
            timestamp=datetime.now(timezone.utc),
        )

        # Thumbnail hinzufügen falls gewünscht
        if include_thumbnail:
            image_url = None

            # Zuerst aus Enclosures versuchen
            image_url = cls._extract_enclosure_image(entry)

            # Falls kein Enclosure-Bild, aus HTML-Summary extrahieren
            if not image_url and hasattr(entry, "summary") and entry.summary:
                image_url = cls._extract_image_url(entry.summary)

            if image_url:
                embed.set_thumbnail(url=image_url)

        # Kategorie hinzufügen falls gewünscht (hauptsächlich für Hardwareluxx)
        if include_category and hasattr(entry, "tags") and entry.tags:
            category = entry.tags[0].get("term", "")
            if category:
                embed.add_field(name="Kategorie", value=category, inline=True)

        # Beschreibung hinzufügen falls gewünscht und vorhanden
        if include_description and hasattr(entry, "summary") and entry.summary:
            clean_summary = cls._clean_html_text(entry.summary, max_description_length)
            if clean_summary:
                embed.add_field(name="Beschreibung", value=clean_summary, inline=False)

        # Veröffentlichungsdatum hinzufügen falls vorhanden
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            embed.add_field(
                name="Veröffentlicht",
                value=f"<t:{int(pub_date.timestamp())}:R>",
                inline=True,
            )

        # Footer konfigurieren
        footer_config = cls.RSS_FOOTER_CONFIG.get(source)
        if footer_config:
            embed.set_footer(
                text=footer_config["text"],
                icon_url=footer_config["icon_url"],
            )

        return embed
