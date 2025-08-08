"""
Dekoratoren für Discord-Befehle
"""

from discord.ext import commands
from functools import wraps


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

            from utils.embeds import EmbedFactory

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
