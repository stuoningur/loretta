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

from src.bot.utils.logging import setup_logging
from src.database import DatabaseManager, initialize_database

load_dotenv()

# Richte Logging ein
setup_logging()

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
            command_prefix="!",  # Standard-Prefix, wird durch process_commands überschrieben
            intents=intents,
            help_command=None,
            description="Loretta",
        )

        # Datenbank-Setup
        self.db_path = Path(__file__).parent.parent / "database" / "loretta.db"
        self.db = DatabaseManager(self.db_path)

        # Owner ID Setup
        self.configured_owner_id = None
        owner_id_str = os.getenv("OWNER_ID")
        if owner_id_str:
            try:
                self.configured_owner_id = int(owner_id_str)
                logger.info(f"Bot Owner ID gesetzt auf: {self.configured_owner_id}")
            except ValueError:
                logger.error(
                    f"Ungültige OWNER_ID in Umgebungsvariablen: {owner_id_str}"
                )
        else:
            logger.warning("Keine OWNER_ID in Umgebungsvariablen gesetzt")

    async def is_owner(self, user):
        """Überprüft ob ein Benutzer der Bot-Owner ist"""
        # Verwende konfigurierte Owner-ID falls gesetzt
        if self.configured_owner_id:
            return user.id == self.configured_owner_id

        # Fallback auf Standard-Discord.py is_owner Verhalten
        return await super().is_owner(user)

    async def get_prefix(self, message) -> str:
        """Dynamische Prefix-Funktion die Einstellungen aus der Datenbank lädt"""
        # Behandle Grenzfälle wo Nachricht None sein könnte oder Guild fehlt
        if not message or not hasattr(message, "guild") or not message.guild:
            return "!"  # Standard-Prefix für DMs oder ungültige Messages

        try:
            config = await self.db.get_guild_config(message.guild.id)
            return config.command_prefix
        except Exception as e:
            logger.error(
                f"Fehler beim Laden des Prefix für Server {message.guild.id}: {e}"
            )
            return "!"  # Rückfall auf Standard-Prefix

    async def setup_hook(self):
        """Wird beim Bot-Start ausgeführt"""
        logger.info("Bot wird initialisiert...")

        # Initialisiere Datenbank
        try:
            await initialize_database(self.db_path)
            logger.info("Datenbank erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankinitialisierung: {e}")
            raise

        # Lade alle Cogs automatisch aus allen Unterverzeichnissen
        loaded_cogs = 0
        failed_cogs = 0

        # Automatische Erkennung aller Cog-Module
        cogs_dir = Path(__file__).parent / "cogs"
        
        def discover_cogs():
            """Entdeckt alle Python-Dateien in den Cog-Verzeichnissen"""
            cog_modules = []
            
            for py_file in cogs_dir.rglob("*.py"):
                # Überspringe __init__.py Dateien
                if py_file.name == "__init__.py":
                    continue
                
                # Erstelle Modulpfad relativ zum src Verzeichnis
                relative_path = py_file.relative_to(Path(__file__).parent.parent.parent)
                module_path = ".".join(relative_path.with_suffix("").parts)
                
                # Bestimme Kategorie aus dem Verzeichnisnamen
                category = py_file.parent.name
                cog_name = py_file.stem
                
                cog_modules.append((category, cog_name, module_path))
            
            return sorted(cog_modules)

        # Entdecke und lade alle Cogs
        discovered_cogs = discover_cogs()
        current_category = None
        
        for category, _, module_path in discovered_cogs:
            # Logge Kategorie-Header nur einmal
            if category != current_category:
                logger.info(f"Lade {category.title()} Cogs...")
                current_category = category
            
            try:
                await self.load_extension(module_path)
                loaded_cogs += 1
                logger.debug(f"✓ {module_path} erfolgreich geladen")
            except Exception as e:
                logger.error(f"✗ Fehler beim Laden von '{module_path}': {e}")
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
                # Server Command-Tree löschen
                self.tree.clear_commands(guild=guild)
                # Kopiere globale Commands zu jeden Server für sofortige Verfügbarkeit
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                total_synced += len(synced)
                logger.info(
                    f"Command-Tree geleert und Slash-Commands für Server '{guild.name}' synchronisiert: {len(synced)} Commands"
                )

            logger.info(f"Gesamt synchronisierte Commands: {total_synced}")
        except Exception as e:
            logger.error(f"Fehler beim Synchronisieren der Slash-Commands: {e}")

    async def on_guild_join(self, guild):
        """Wird ausgeführt wenn der Bot einem Server beitritt"""
        logger.info(f'Bot ist dem Server "{guild.name}" (ID: {guild.id}) beigetreten')

        # Erstelle Standardkonfiguration für neuen Server
        try:
            config = await self.db.get_guild_config(guild.id)
            await self.db.set_guild_config(config)
            logger.info(f"Standardkonfiguration für Server {guild.id} erstellt")
        except Exception as e:
            logger.error(
                f"Fehler beim Erstellen der Serverkonfiguration für {guild.id}: {e}"
            )

    async def on_guild_remove(self, guild):
        """Wird ausgeführt wenn der Bot einen Server verlässt"""
        logger.info(f'Bot hat den Server "{guild.name}" (ID: {guild.id}) verlassen')

    async def process_commands(self, message):
        """Überschreibt process_commands für dynamische Prefix-Behandlung"""
        if message.author.bot:
            return

        # Lade dynamischen Prefix
        prefix = await self.get_prefix(message)

        # Setze temporär den command_prefix für diese Nachricht
        original_prefix = self.command_prefix
        self.command_prefix = prefix

        try:
            # Verarbeite Commands mit dem dynamischen Prefix
            await super().process_commands(message)
        finally:
            # Stelle ursprünglichen Prefix wieder her
            self.command_prefix = original_prefix

    async def on_message(self, message):
        """Wird bei jeder Nachricht ausgeführt"""
        await self.process_commands(message)


class KeyboardInterruptHandler:
    """Handler für graceful shutdown bei SIGINT/SIGTERM"""

    def __init__(self, bot):
        self.bot = bot
        self._task = None
        self._shutdown_initiated = False

    def __call__(self, signum=None, frame=None):
        """Signal-Handler-Rückruf"""
        if self._shutdown_initiated:
            logger.warning("Shutdown bereits eingeleitet, warte auf Abschluss...")
            return

        self._shutdown_initiated = True
        signal_name = signal.Signals(signum).name if signum else "SIGINT"
        logger.info(
            f"Signal {signal_name} empfangen, leite elegantes Herunterfahren ein..."
        )

        # frame Parameter ist für Signal-Handler erforderlich aber nicht verwendet
        _ = frame

        if self._task:
            logger.warning("Herunterfahren-Task läuft bereits")
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

    # Richte elegantes Herunterfahren ein
    shutdown_handler = KeyboardInterruptHandler(bot)

    # Registriere Signal-Handler für graceful shutdown
    if sys.platform != "win32":  # Unix-ähnliche Systeme
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
