#!/usr/bin/env python3
"""
Loretta Discord Bot - Haupteingangspunkt
Ein Discord-Bot mit verschiedenen Utility-Funktionen
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/loretta.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class LorettaBot(commands.Bot):
    """Hauptbot-Klasse für Loretta"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.presences = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            description="Loretta - Ein vielseitiger Discord-Bot",
        )

    async def setup_hook(self):
        """Wird beim Bot-Start ausgeführt"""
        logger.info("Bot wird initialisiert...")

        # Erstelle Datenverzeichnis falls es nicht existiert
        Path("data").mkdir(exist_ok=True)

        # Lade alle Cogs
        try:
            await self.load_extension("cogs.serverinfo")
            logger.info("Cogs erfolgreich geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Cogs: {e}")

    async def on_ready(self):
        """Wird ausgeführt wenn der Bot bereit ist"""
        logger.info(f"{self.user} ist jetzt online!")
        logger.info(f"Bot-ID: {self.user.id if self.user else 'Unbekannt'}")
        logger.info(f"Discord.py Version: {discord.__version__}")
        logger.info(f"Verbunden mit {len(self.guilds)} Servern")

        # Setze Bot-Status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="über die Server"
            )
        )

    async def on_guild_join(self, guild):
        """Wird ausgeführt wenn der Bot einem Server beitritt"""
        logger.info(f'Bot ist dem Server "{guild.name}" (ID: {guild.id}) beigetreten')

    async def on_guild_remove(self, guild):
        """Wird ausgeführt wenn der Bot einen Server verlässt"""
        logger.info(f'Bot hat den Server "{guild.name}" (ID: {guild.id}) verlassen')


class KeyboardInterruptHandler:
    """Handler für graceful shutdown bei SIGINT/SIGTERM"""

    def __init__(self, bot):
        self.bot = bot
        self._task = None
        self._shutdown_initiated = False

    def __call__(self, signum=None, frame=None):
        """Signal handler callback"""
        if self._shutdown_initiated:
            logger.warning("Shutdown bereits eingeleitet, warte auf Abschluss...")
            return

        self._shutdown_initiated = True
        signal_name = signal.Signals(signum).name if signum else "SIGINT"
        logger.info(f"Signal {signal_name} empfangen, leite graceful shutdown ein...")

        if self._task:
            logger.warning("Shutdown-Task läuft bereits")
            return

        self._task = asyncio.create_task(self._shutdown())

    async def _shutdown(self):
        """Führt graceful shutdown durch"""
        try:
            logger.info("Beginne Bot-Herunterfahren...")
            await self.bot.close()
            logger.info("Bot erfolgreich heruntergefahren")
        except Exception as e:
            logger.error(f"Fehler beim Herunterfahren des Bots: {e}", exc_info=True)


async def main():
    """Hauptfunktion zum Starten des Bots"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN nicht in Umgebungsvariablen gefunden!")
        return 1

    bot = LorettaBot()

    # Setup graceful shutdown
    shutdown_handler = KeyboardInterruptHandler(bot)

    # Registriere Signal-Handler für graceful shutdown
    if sys.platform != "win32":  # Unix-like systems
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown_handler, sig, None)
    else:  # Windows
        signal.signal(signal.SIGINT, shutdown_handler)

    try:
        async with bot:
            logger.info("Bot startet...")
            await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot-Herunterfahren durch KeyboardInterrupt")
    except Exception as error:
        logger.error(f"Fataler Fehler: {error}", exc_info=True)
        return 1
    finally:
        logger.info("Bot-Hauptschleife beendet")

    return 0


if __name__ == "__main__":
    asyncio.run(main())
