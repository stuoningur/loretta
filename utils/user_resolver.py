"""
Benutzer-Auflösungs-Utilities für Discord-Bots
"""

import discord
from discord.ext import commands
from typing import Optional, Union, List
from utils.embeds import EmbedFactory


class UserResolver:
    """Utility-Klasse für das Auflösen von Discord-Benutzern aus verschiedenen Eingabeformaten"""

    @staticmethod
    async def resolve_user_by_mention(
        ctx: commands.Context, user_input: str
    ) -> Optional[Union[discord.Member, discord.User]]:
        """Löst Benutzer aus Erwähnungsformat auf (<@12345> oder @12345)"""
        # Extrahiere Ziffern aus Erwähnung
        user_id_str = "".join(filter(str.isdigit, user_input))
        if not user_id_str:
            return None

        try:
            user_id = int(user_id_str)
        except ValueError:
            await ctx.send(
                embed=EmbedFactory.error_embed(
                    "Ungültige Benutzer-ID", "Die Benutzer-ID ist ungültig."
                )
            )
            return None

        # Versuche zuerst als Guild-Mitglied zu holen (schneller)
        if ctx.guild:
            target_user = ctx.guild.get_member(user_id)
            if target_user:
                return target_user

        # Rückfall auf API-Abruf
        try:
            return await ctx.bot.fetch_user(user_id)
        except (discord.NotFound, discord.HTTPException):
            await ctx.send(
                embed=EmbedFactory.error_embed(
                    "Benutzer nicht gefunden",
                    "Der angegebene Benutzer konnte nicht gefunden werden.",
                )
            )
            return None

    @staticmethod
    def find_users_by_display_name(
        guild: discord.Guild, search_term: str
    ) -> List[discord.Member]:
        """Findet Guild-Mitglieder nach Anzeigename (groß-/kleinschreibungsunabhängige Teilsuche)"""
        search_term = search_term.lower().strip()
        return [
            member
            for member in guild.members
            if search_term in member.display_name.lower()
        ]

    @staticmethod
    def find_users_by_username(
        guild: discord.Guild, search_term: str
    ) -> List[discord.Member]:
        """Findet Guild-Mitglieder nach Benutzername oder Benutzername#Diskriminator"""
        search_term = search_term.lower().strip()

        # Prüfe auf Benutzername#Diskriminator-Format
        if "#" in search_term:
            parts = search_term.split("#", 1)
            if len(parts) == 2:
                username, discriminator = parts
                return [
                    member
                    for member in guild.members
                    if (
                        member.name.lower() == username.lower()
                        and member.discriminator == discriminator
                    )
                ]

        # Teilweise Benutzername-Übereinstimmung
        return [
            member for member in guild.members if search_term in member.name.lower()
        ]

    @staticmethod
    async def resolve_user_by_name_search(
        ctx: commands.Context, search_term: str
    ) -> Optional[discord.Member]:
        """Löst Benutzer durch Suche nach Anzeigename und Benutzername auf"""
        if not ctx.guild:
            await ctx.send(
                embed=EmbedFactory.error_embed(
                    "Fehler", "Benutzersuche ist nur in Servern möglich."
                )
            )
            return None

        # Versuche zuerst Anzeigename-Suche
        display_matches = UserResolver.find_users_by_display_name(
            ctx.guild, search_term
        )

        # Versuche Benutzername-Suche wenn keine Anzeigename-Übereinstimmungen
        username_matches = UserResolver.find_users_by_username(ctx.guild, search_term)

        # Kombiniere Ergebnisse, priorisiere Anzeigename-Übereinstimmungen
        all_matches = display_matches + [
            m for m in username_matches if m not in display_matches
        ]

        if not all_matches:
            await ctx.send(
                embed=EmbedFactory.error_embed(
                    "Benutzer nicht gefunden",
                    "Das Servermitglied konnte nicht gefunden werden.",
                )
            )
            return None

        if len(all_matches) == 1:
            return all_matches[0]

        # Mehrere Übereinstimmungen - zeige Unterscheidung
        match_list = "\n".join(
            [
                f"• {member.display_name} (`{member.name}#{member.discriminator}`)"
                for member in all_matches[
                    :10
                ]  # Begrenze auf erste 10 Übereinstimmungen
            ]
        )

        if len(all_matches) > 10:
            match_list += f"\n... und {len(all_matches) - 10} weitere"

        await ctx.send(
            embed=EmbedFactory.error_embed(
                "Mehrere Benutzer gefunden",
                f"Mehrere Servermitglieder gefunden, bitte schränke die Suche ein:\n\n{match_list}",
            )
        )
        return None

    @staticmethod
    async def resolve_user(
        ctx: commands.Context, user_input: str
    ) -> Optional[Union[discord.Member, discord.User]]:
        """Löst einen Benutzer aus Eingabestring auf (Erwähnung, Benutzername oder Anzeigename)"""
        user_input = user_input.strip()

        # Versuche zuerst Erwähnungsformat (spezifischste)
        if "@" in user_input or user_input.isdigit():
            return await UserResolver.resolve_user_by_mention(ctx, user_input)

        # Versuche namensbasierte Suche
        return await UserResolver.resolve_user_by_name_search(ctx, user_input)
