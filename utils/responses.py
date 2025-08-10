"""
Utility-Funktionen für Discord-Interaction-Responses
"""

import logging
from typing import Optional, Union

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


async def send_response(
    ctx: Union[commands.Context, discord.Interaction],
    embed: discord.Embed,
    ephemeral: bool = False,
    content: Optional[str] = None,
) -> Optional[discord.Message]:
    """
    Sendet eine Response über den angemessensten Weg basierend auf dem Context-Typ

    Args:
        ctx: Context oder Interaction
        embed: Embed zum Senden
        ephemeral: Ob die Nachricht ephemeral sein soll (nur für Slash Commands)
        content: Optionaler Text-Inhalt zusätzlich zum Embed

    Returns:
        Message-Objekt falls verfügbar, None andernfalls
    """
    try:
        if isinstance(ctx, discord.Interaction):
            # Slash Command Interaction
            if ctx.response.is_done():
                if content is not None:
                    return await ctx.followup.send(
                        content=content, embed=embed, ephemeral=ephemeral
                    )
                else:
                    return await ctx.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                if content is not None:
                    await ctx.response.send_message(
                        content=content, embed=embed, ephemeral=ephemeral
                    )
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=ephemeral)
                # Für defer followup
                if ephemeral:
                    return None
                else:
                    return await ctx.original_response()

        elif isinstance(ctx, commands.Context):
            # Traditional Command Context
            if ctx.interaction:
                # Hybrid Command mit Slash
                if ctx.interaction.response.is_done():
                    if content is not None:
                        return await ctx.interaction.followup.send(
                            content=content, embed=embed, ephemeral=ephemeral
                        )
                    else:
                        return await ctx.interaction.followup.send(
                            embed=embed, ephemeral=ephemeral
                        )
                else:
                    if content is not None:
                        await ctx.interaction.response.send_message(
                            content=content, embed=embed, ephemeral=ephemeral
                        )
                    else:
                        await ctx.interaction.response.send_message(
                            embed=embed, ephemeral=ephemeral
                        )
                    if not ephemeral:
                        return await ctx.interaction.original_response()
            else:
                # Traditional Prefix Command
                if content is not None:
                    return await ctx.send(content=content, embed=embed)
                else:
                    return await ctx.send(embed=embed)

        return None

    except Exception as e:
        logger.error(f"Fehler beim Senden der Response: {e}")
        # Fallback: Versuche normalen send
        try:
            if isinstance(ctx, commands.Context):
                if content is not None:
                    return await ctx.send(content=content, embed=embed)
                else:
                    return await ctx.send(embed=embed)
        except Exception as fallback_error:
            logger.error(f"Fallback-Response fehlgeschlagen: {fallback_error}")
        return None


async def send_error_response(
    ctx: Union[commands.Context, discord.Interaction],
    title: str,
    description: str,
    ephemeral: bool = True,
) -> Optional[discord.Message]:
    """
    Sendet eine Fehler-Response

    Args:
        ctx: Context oder Interaction
        title: Fehler-Titel
        description: Fehler-Beschreibung
        ephemeral: Ob die Nachricht ephemeral sein soll

    Returns:
        Message-Objekt falls verfügbar
    """
    from utils.embeds import EmbedFactory

    embed = EmbedFactory.error_embed(title, description)
    return await send_response(ctx, embed, ephemeral)


async def send_success_response(
    ctx: Union[commands.Context, discord.Interaction],
    title: str,
    description: str,
    ephemeral: bool = False,
) -> Optional[discord.Message]:
    """
    Sendet eine Erfolgs-Response

    Args:
        ctx: Context oder Interaction
        title: Erfolgs-Titel
        description: Erfolgs-Beschreibung
        ephemeral: Ob die Nachricht ephemeral sein soll

    Returns:
        Message-Objekt falls verfügbar
    """
    from utils.embeds import EmbedFactory

    embed = EmbedFactory.success_embed(title, description)
    return await send_response(ctx, embed, ephemeral)


async def send_info_response(
    ctx: Union[commands.Context, discord.Interaction],
    title: str,
    description: str,
    ephemeral: bool = False,
) -> Optional[discord.Message]:
    """
    Sendet eine Info-Response

    Args:
        ctx: Context oder Interaction
        title: Info-Titel
        description: Info-Beschreibung
        ephemeral: Ob die Nachricht ephemeral sein soll

    Returns:
        Message-Objekt falls verfügbar
    """
    from utils.embeds import EmbedFactory

    embed = EmbedFactory.info_embed(title, description)
    return await send_response(ctx, embed, ephemeral)


async def defer_response(
    ctx: Union[commands.Context, discord.Interaction],
    ephemeral: bool = False,
) -> bool:
    """
    Deferiert eine Response falls notwendig

    Args:
        ctx: Context oder Interaction
        ephemeral: Ob die Response ephemeral sein soll

    Returns:
        True wenn erfolgreich deferiert, False andernfalls
    """
    try:
        if isinstance(ctx, discord.Interaction):
            if not ctx.response.is_done():
                await ctx.response.defer(ephemeral=ephemeral)
                return True
        elif isinstance(ctx, commands.Context) and ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.defer(ephemeral=ephemeral)
                return True
        return False
    except Exception as e:
        logger.error(f"Fehler beim Deferieren der Response: {e}")
        return False
