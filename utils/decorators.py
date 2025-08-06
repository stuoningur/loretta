"""
Decorators for Discord commands
"""

from discord.ext import commands
from functools import wraps


def guild_only():
    """Decorator to ensure command is only used in guilds"""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            if not ctx.guild:
                from utils.embeds import EmbedFactory

                embed = EmbedFactory.error_embed(
                    "Fehler", "Dieser Befehl kann nur in einem Server verwendet werden."
                )
                await ctx.send(embed=embed)
                return
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def validate_input(
    min_length: int = 1, max_length: int = 2000, field_name: str = "Eingabe"
):
    """Decorator for input validation"""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            # Find the input parameter (usually the last positional arg or in kwargs)
            input_text = None
            if args:
                # Get last argument which is usually the input text
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
