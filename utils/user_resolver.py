"""
User resolution utilities for Discord bots
"""

import discord
from discord.ext import commands
from typing import Optional, Union, List
from utils.embeds import EmbedFactory


class UserResolver:
    """Utility class for resolving Discord users from various input formats"""

    @staticmethod
    async def resolve_user_by_mention(
        ctx: commands.Context, user_input: str
    ) -> Optional[Union[discord.Member, discord.User]]:
        """Resolve user from mention format (<@12345> or @12345)"""
        # Extract digits from mention
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

        # Try to get as guild member first (faster)
        if ctx.guild:
            target_user = ctx.guild.get_member(user_id)
            if target_user:
                return target_user

        # Fallback to API fetch
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
        """Find guild members by display name (case-insensitive partial match)"""
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
        """Find guild members by username or username#discriminator"""
        search_term = search_term.lower().strip()

        # Check for username#discriminator format
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

        # Partial username match
        return [
            member for member in guild.members if search_term in member.name.lower()
        ]

    @staticmethod
    async def resolve_user_by_name_search(
        ctx: commands.Context, search_term: str
    ) -> Optional[discord.Member]:
        """Resolve user by searching display name and username"""
        if not ctx.guild:
            await ctx.send(
                embed=EmbedFactory.error_embed(
                    "Fehler", "Benutzersuche ist nur in Servern möglich."
                )
            )
            return None

        # Try display name search first
        display_matches = UserResolver.find_users_by_display_name(
            ctx.guild, search_term
        )

        # Try username search if no display name matches
        username_matches = UserResolver.find_users_by_username(ctx.guild, search_term)

        # Combine results, prioritizing display name matches
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

        # Multiple matches - show disambiguation
        match_list = "\n".join(
            [
                f"• {member.display_name} (`{member.name}#{member.discriminator}`)"
                for member in all_matches[:10]  # Limit to first 10 matches
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
        """Resolve a user from input string (mention, username, or display name)"""
        user_input = user_input.strip()

        # Try mention format first (most specific)
        if "@" in user_input or user_input.isdigit():
            return await UserResolver.resolve_user_by_mention(ctx, user_input)

        # Try name-based search
        return await UserResolver.resolve_user_by_name_search(ctx, user_input)
