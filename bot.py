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

from models.database import initialize_database
from utils.database import DatabaseManager

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
            command_prefix=self.get_prefix,  # type: ignore
            intents=intents,
            help_command=None,
            description="Loretta - Ein vielseitiger Discord-Bot",
        )

        # Database setup
        self.db_path = os.getenv("DATABASE_PATH", "data/loretta.db")
        self.db = DatabaseManager(self.db_path)

    async def get_prefix(self, message):
        """Dynamische Prefix-Funktion die Einstellungen aus der Datenbank lädt"""
        # Handle edge cases where message might be None or missing guild
        if not message or not hasattr(message, "guild") or not message.guild:
            return "!"  # Standard-Prefix für DMs oder ungültige Messages

        try:
            config = await self.db.get_server_config(message.guild.id)
            return config.command_prefix
        except Exception as e:
            logger.error(
                f"Fehler beim Laden des Prefix für Server {message.guild.id}: {e}"
            )
            return "!"  # Fallback auf Standard-Prefix

    async def setup_hook(self):
        """Wird beim Bot-Start ausgeführt"""
        logger.info("Bot wird initialisiert...")

        # Erstelle Datenverzeichnis falls es nicht existiert
        Path("data").mkdir(exist_ok=True)

        # Initialisiere Datenbank
        try:
            await initialize_database(self.db_path)
            logger.info("Datenbank erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankinitialisierung: {e}")
            raise

        # Lade alle Cogs automatisch aus dem cogs-Ordner
        cogs_dir = Path("cogs")
        loaded_cogs = 0
        failed_cogs = 0

        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.name.startswith("__"):
                continue

            cog_name = f"cogs.{cog_file.stem}"
            try:
                await self.load_extension(cog_name)
                loaded_cogs += 1
            except Exception as e:
                logger.error(f"Fehler beim Laden von Cog '{cog_name}': {e}")
                failed_cogs += 1

        logger.info(
            f"Cog-Ladevorgang abgeschlossen: {loaded_cogs} erfolgreich, {failed_cogs} fehlgeschlagen"
        )

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

        # Synchronisiere Slash-Commands
        try:
            # Sync für jeden Server einzeln (sofort verfügbar)
            total_synced = 0
            for guild in self.guilds:
                # Kopiere globale Commands zu jeden Server für sofortige Verfügbarkeit
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                total_synced += len(synced)
                logger.info(
                    f"Slash-Commands für Server '{guild.name}' synchronisiert: {len(synced)} Commands"
                )

            logger.info(f"Gesamt synchronisierte Commands: {total_synced}")
        except Exception as e:
            logger.error(f"Fehler beim Synchronisieren der Slash-Commands: {e}")

    async def on_guild_join(self, guild):
        """Wird ausgeführt wenn der Bot einem Server beitritt"""
        logger.info(f'Bot ist dem Server "{guild.name}" (ID: {guild.id}) beigetreten')

        # Erstelle Standardkonfiguration für neuen Server
        try:
            config = await self.db.get_server_config(guild.id)
            await self.db.set_server_config(config)
            logger.info(f"Standardkonfiguration für Server {guild.id} erstellt")
        except Exception as e:
            logger.error(
                f"Fehler beim Erstellen der Serverkonfiguration für {guild.id}: {e}"
            )

    async def on_guild_remove(self, guild):
        """Wird ausgeführt wenn der Bot einen Server verlässt"""
        logger.info(f'Bot hat den Server "{guild.name}" (ID: {guild.id}) verlassen')

    async def on_message(self, message):
        """Wird bei jeder Nachricht ausgeführt"""
        # Ignoriere Bot-Nachrichten
        if message.author.bot:
            return

        # Verarbeite Commands normal
        await self.process_commands(message)


class KeyboardInterruptHandler:
    """Handler für graceful shutdown bei SIGINT/SIGTERM"""

    def __init__(self, bot):
        self.bot = bot
        self._task = None
        self._shutdown_initiated = False

    def __call__(self, signum=None, _frame=None):
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
