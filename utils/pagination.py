"""
Wiederverwendbare Paginierungs-Utilities für Discord-Bots
"""

import discord
import logging
from typing import Optional, Union, Callable, Any
from abc import ABC, abstractmethod

# Constants
DEFAULT_TIMEOUT = 180
FIRST_PAGE = 0
DEFAULT_RESULTS_PER_PAGE = 2
MAX_EMBED_DESCRIPTION_LENGTH = 4000
TRUNCATION_SUFFIX = "\n..."

logger = logging.getLogger(__name__)


class PaginationView(discord.ui.View, ABC):
    """Abstrakte Basis-Klasse für Paginierungs-Views"""

    def __init__(
        self,
        requester: Union[discord.Member, discord.User],
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(timeout=timeout)
        self.requester = requester
        self.current_page = FIRST_PAGE
        self.total_pages = FIRST_PAGE
        self.message: Optional[discord.Message] = None

    @abstractmethod
    async def get_page_embed(self, page: int) -> discord.Embed:
        """Holt Embed für eine bestimmte Seite - muss von Unterklassen implementiert werden"""
        pass

    async def update_buttons(self):
        """Aktualisiert Button-Zustände basierend auf aktueller Seite"""
        self.previous_button.disabled = self.current_page == FIRST_PAGE
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    @discord.ui.button(label="← Vorherige", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page > FIRST_PAGE:
            self.current_page -= 1
            embed = await self.get_page_embed(self.current_page)
            await self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Nächste →", style=discord.ButtonStyle.secondary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            embed = await self.get_page_embed(self.current_page)
            await self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Löschen", style=discord.ButtonStyle.danger)
    async def delete_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Erlaube nur dem Anforderer zu löschen
        if interaction.user.id != self.requester.id:
            await interaction.response.send_message(
                "Nur die Person, die die Suche gestartet hat, kann diese löschen.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content="Ergebnisse wurden gelöscht.", embed=None, view=None
        )

    async def on_timeout(self):
        """Wird aufgerufen wenn der View abgeläuft ist"""
        # Deaktiviere alle Buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Versuche die Nachricht zu bearbeiten um deaktivierte Buttons anzuzeigen
        try:
            embed = await self.get_page_embed(self.current_page)
            embed.set_footer(text="Diese Funktion ist abgelaufen.")
            if hasattr(self, "message") and self.message:
                await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            # Nachricht wurde gelöscht, nichts zu tun
            pass
        except discord.HTTPException:
            # Bearbeitung fehlgeschlagen, aber das ist okay
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Prüft ob die Interaktion gültig ist und behandelt Fehler elegant"""
        # Erlaube nur dem Anforderer die Buttons zu verwenden
        if interaction.user.id != self.requester.id:
            await interaction.response.send_message(
                "Du kannst nur deine eigenen Funktionen verwenden.", ephemeral=True
            )
            return False
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        """Behandelt Interaktionsfehler elegant"""
        logger.error(f"View-Interaktions-Fehler: {error}")

        # Prüfe ob dies ein "unbekannte Interaktion"-Fehler ist (Bot-Neustart)
        if "unknown interaction" in str(error).lower():
            try:
                from utils.embeds import EmbedFactory

                embed = EmbedFactory.error_embed(
                    "Funktion nicht mehr verfügbar",
                    "Die Buttons funktionieren nicht mehr, da der Bot neu gestartet wurde. Führe den Befehl erneut aus.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.HTTPException:
                pass  # Falls wir nicht antworten können, ignoriere einfach
        else:
            try:
                await interaction.response.send_message(
                    "Es ist ein Fehler bei der Funktion aufgetreten.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass


class SearchPaginationView(PaginationView):
    """Paginierungs-View für Suchergebnisse"""

    def __init__(
        self,
        search_function: Callable[
            [int, int], Any
        ],  # Funktion um Ergebnisse zu holen (Limit, Offset)
        guild: discord.Guild,
        search_term: str,
        requester: Union[discord.Member, discord.User],
        results_per_page: int = DEFAULT_RESULTS_PER_PAGE,
        current_page: int = FIRST_PAGE,
    ):
        super().__init__(requester)
        self.search_function = search_function
        self.guild = guild
        self.search_term = search_term
        self.results_per_page = results_per_page
        self.current_page = current_page
        self.total_results = FIRST_PAGE

    async def get_page_embed(self, page: int) -> discord.Embed:
        """Holt Embed für eine bestimmte Seite"""
        from utils.embeds import EmbedFactory

        offset = page * self.results_per_page
        results, total_count = await self.search_function(self.results_per_page, offset)

        self.total_results = total_count
        self.total_pages = max(
            1, (total_count + self.results_per_page - 1) // self.results_per_page
        )

        if not results:
            return EmbedFactory.error_embed(
                "Keine Ergebnisse", f"Keine Einträge mit '{self.search_term}' gefunden."
            )

        # Sammle aktive Guild-Mitglieder
        guild_members = []
        for user_id, _ in results:
            member = self.guild.get_member(user_id)
            if member is not None:
                guild_members.append(member.display_name)

        if not guild_members:
            return EmbedFactory.error_embed(
                "Keine aktiven Benutzer",
                f"Alle gefundenen Benutzer mit '{self.search_term}' sind nicht mehr im Server.",
            )

        # Erstelle paginierte Beschreibung
        description = "\n".join(guild_members)
        if len(description) > MAX_EMBED_DESCRIPTION_LENGTH:
            description = description[:MAX_EMBED_DESCRIPTION_LENGTH] + TRUNCATION_SUFFIX

        embed = EmbedFactory.info_embed(f"Suche nach: {self.search_term}", description)

        embed.add_field(
            name="Auf dieser Seite:",
            value=f"{len(guild_members)} Einträge",
            inline=True,
        )

        embed.add_field(
            name="Insgesamt:",
            value=f"{self.total_results} Einträge gefunden",
            inline=True,
        )

        if self.total_pages > 1:
            embed.add_field(
                name="Seite:",
                value=f"{page + 1} / {self.total_pages}",
                inline=True,
            )

        embed.set_footer(
            text=f"Angefordert von {self.requester.display_name}",
            icon_url=self.requester.display_avatar.url,
        )

        return embed
