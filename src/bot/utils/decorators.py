"""
Dekoratoren für Discord-Befehle
"""

import logging
from functools import wraps
from typing import Union

import discord
from discord.ext import commands

from src.database import CommandStatistic

logger = logging.getLogger(__name__)


def validate_input(
    min_length: int = 1, max_length: int = 2000, field_name: str = "Eingabe"
):
    """Dekorator für Eingabe-Validierung"""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            # Finde den Eingabe-Parameter (normalerweise das letzte Positions-Argument oder in kwargs)
            input_text = None
            if args:
                # Hole letztes Argument welches normalerweise der Eingabe-Text ist
                input_text = args[-1] if args else None
            elif "input_text" in kwargs:
                input_text = kwargs["input_text"]
            elif "text" in kwargs:
                input_text = kwargs["text"]
            elif "search_term" in kwargs:
                input_text = kwargs["search_term"]
            elif "specs_text" in kwargs:
                input_text = kwargs["specs_text"]

            if input_text is None:
                return await func(self, ctx, *args, **kwargs)

            input_text = (
                input_text.strip() if isinstance(input_text, str) else input_text
            )

            from bot.utils.embeds import EmbedFactory

            if not input_text:
                embed = EmbedFactory.error_embed(
                    "Ungültige Eingabe", f"{field_name} darf nicht leer sein."
                )
                await ctx.send(embed=embed)
                return

            if len(input_text) < min_length:
                embed = EmbedFactory.error_embed(
                    f"{field_name} zu kurz",
                    f"{field_name} muss mindestens {min_length} Zeichen lang sein.",
                )
                await ctx.send(embed=embed)
                return

            if len(input_text) > max_length:
                embed = EmbedFactory.error_embed(
                    f"{field_name} zu lang",
                    f"{field_name} darf maximal {max_length} Zeichen lang sein.",
                )
                await ctx.send(embed=embed)
                return

            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def track_command_usage(func):
    """
    Dekorator zum Verfolgen der Command-Nutzung und -Statistiken.
    Protokolliert automatisch Command-Ausführungen in der Datenbank.
    """

    @wraps(func)
    async def wrapper(
        self, ctx: Union[commands.Context, discord.Interaction], *args, **kwargs
    ):
        success = True
        error_message = None

        # Bestimme guild_id und user_id basierend auf dem Kontext-Typ
        if isinstance(ctx, commands.Context):
            guild_id = ctx.guild.id if ctx.guild else 0
            user_id = ctx.author.id
            user = ctx.author
            guild = ctx.guild
        else:  # discord.Interaction
            guild_id = ctx.guild.id if ctx.guild else 0
            user_id = ctx.user.id
            user = ctx.user
            guild = ctx.guild

        # Command-Namen aus der Funktion ermitteln
        command_name = func.__name__
        cog_name = self.__class__.__name__ if hasattr(self, "__class__") else None

        try:
            # Führe den ursprünglichen Command aus
            result = await func(self, ctx, *args, **kwargs)
            return result
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Command {command_name} fehlgeschlagen: {e}")
            raise  # Re-raise die Exception damit normale Error-Handler funktionieren
        finally:
            # Erstelle CommandStatistic-Objekt
            stat = CommandStatistic(
                id=None,
                guild_id=guild_id,
                user_id=user_id,
                command_name=command_name,
                cog_name=cog_name,
                success=success,
                error_message=error_message if not success else None,
            )

            # Protokolliere in Datenbank (falls Bot verfügbar ist)
            try:
                if hasattr(self, "bot") and hasattr(self.bot, "db"):
                    await self.bot.db.log_command_usage(stat, user, guild)
            except Exception as e:
                # Fehler beim Logging sollten den Command nicht beeinträchtigen
                logger.error(f"Fehler beim Protokollieren der Command-Statistik: {e}")

    return wrapper
