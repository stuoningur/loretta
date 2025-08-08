"""
Leetspeak Befehl für den Loretta Discord Bot
"""

import logging

from discord.ext import commands
from utils.decorators import track_command_usage


logger = logging.getLogger(__name__)


class Leetspeak(commands.Cog):
    """Leetspeak Befehl für 1337 sp34k Konvertierung"""

    def __init__(self, bot):
        self.bot = bot

        # Leet speak Übersetzungstabelle
        self.leet_map = {
            "a": "4",
            "A": "4",
            "b": "8",
            "B": "8",
            "e": "3",
            "E": "3",
            "g": "6",
            "G": "6",
            "i": "1",
            "I": "1",
            "l": "1",
            "L": "1",
            "o": "0",
            "O": "0",
            "s": "5",
            "S": "5",
            "t": "7",
            "T": "7",
            "z": "2",
            "Z": "2",
        }

    @commands.hybrid_command(
        name="leetspeak",
        aliases=["leet", "1337"],
        description="Konvertiert Text zu Leet Speak (1337 sp34k)",
    )
    @track_command_usage
    async def leetspeak(self, ctx, *, text: str):
        """Konvertiert den eingegebenen Text zu Leet Speak"""

        try:
            # Konvertiere Text zu Leet Speak
            leet_text = "".join(self.leet_map.get(char, char) for char in text)

            # Sende den Leet Speak Text direkt
            await ctx.send(leet_text)

            logger.info(
                f"Leetspeak-Befehl ausgeführt von {ctx.author} mit Text: '{text[:50]}...'"
            )

        except Exception as e:
            logger.error(f"Fehler beim Konvertieren zu Leet Speak: {e}")
            await ctx.send("Fehler beim Konvertieren zu Leet Speak.")


async def setup(bot):
    """Lädt das Leetspeak Cog"""
    await bot.add_cog(Leetspeak(bot))
    logger.info("Leetspeak Cog geladen")
