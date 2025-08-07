#!/usr/bin/env python3
"""
Loretta Discord Bot - Haupteingangspunkt
Ein Discord-Bot mit verschiedenen Utility-Funktionen
"""

import asyncio
import logging
import logging.handlers
import os
import signal
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from models.database import initialize_database
from utils.database import DatabaseManager
from utils.embeds import EmbedFactory

load_dotenv()


class ColoredConsoleHandler(logging.StreamHandler):
    """Custom handler that adds color to console output using ANSI escape codes"""

    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging():
    """Setup logging with rotating files and colored console output"""
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    # Create formatters
    logging_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # Remove any existing handlers

    # File handler with rotation (10MB max, keep 5 backup files)
    file_handler = logging.handlers.RotatingFileHandler(
        "data/loretta.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging_formatter)
    file_handler.setLevel(log_level)

    # Colored console handler
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(logging_formatter)
    console_handler.setLevel(log_level)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


# Setup logging
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

    async def on_command_error(self, ctx, error):
        """Globaler Error Handler für alle Commands"""
        # Verhindere Mehrfachbehandlung von Fehlern wenn Cogs eigene Handler haben
        if hasattr(ctx.command, "on_error"):
            return

        # Original Exception extrahieren falls vorhanden
        error = getattr(error, "original", error)

        # Log den Fehler für Debugging (ohne full traceback für bekannte Fehler)
        if isinstance(
            error,
            (
                commands.CommandNotFound,
                commands.MissingRequiredArgument,
                commands.BadArgument,
                commands.TooManyArguments,
                commands.MissingPermissions,
                commands.BotMissingPermissions,
                commands.CommandOnCooldown,
                commands.NoPrivateMessage,
                commands.PrivateMessageOnly,
                commands.DisabledCommand,
                commands.NotOwner,
                commands.CheckFailure,
                discord.HTTPException,
            ),
        ):
            # Für bekannte Fehler nur basic logging ohne traceback
            pass
        else:
            # Für unbekannte Fehler full logging mit traceback
            logger.error(
                f"Command error in {ctx.command}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung
        if isinstance(error, commands.CommandNotFound):
            # Extrahiere den Befehlsnamen aus der Nachricht
            prefix = await self.get_prefix(ctx.message)
            if isinstance(prefix, list):
                prefix = prefix[0]  # Nimm ersten Prefix
            command_name = ctx.message.content[len(prefix) :].split()[0]
            logger.info(
                f"Command not found: '{command_name}' by {ctx.author} ({ctx.author.id}) in {ctx.guild.name if ctx.guild else 'DM'}"
            )
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, commands.MissingRequiredArgument):
            param_name = getattr(getattr(error, "param", None), "name", "unbekannt")
            logger.warning(
                f"Missing required argument '{param_name}' in command {ctx.command} by {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.missing_argument_embed(param_name)

        elif isinstance(error, commands.BadArgument):
            # Versuche den Parameternamen und erwarteten Typ zu extrahieren
            param_name = getattr(getattr(error, "param", None), "name", "unbekannt")
            expected_type = "gültiger Wert"

            # Spezifische Typen identifizieren
            if "int" in str(error).lower():
                expected_type = "ganze Zahl"
            elif "float" in str(error).lower():
                expected_type = "Dezimalzahl"
            elif "member" in str(error).lower():
                expected_type = "Benutzername oder Erwähnung"
            elif "channel" in str(error).lower():
                expected_type = "Kanalname oder Erwähnung"
            elif "role" in str(error).lower():
                expected_type = "Rollenname oder Erwähnung"

            logger.warning(
                f"Bad argument '{param_name}' (expected: {expected_type}) in command {ctx.command} by {ctx.author} ({ctx.author.id}): {str(error)}"
            )
            embed = EmbedFactory.bad_argument_embed(param_name, expected_type)

        elif isinstance(error, commands.TooManyArguments):
            logger.warning(
                f"Too many arguments provided for command {ctx.command} by {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.too_many_arguments_embed()

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.warning(
                f"Missing permissions ({missing_perms}) for command {ctx.command} by {ctx.author} ({ctx.author.id}) in {ctx.guild.name if ctx.guild else 'DM'}"
            )
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.error(
                f"Bot missing permissions ({missing_perms}) for command {ctx.command} in {ctx.guild.name if ctx.guild else 'DM'} (Guild ID: {ctx.guild.id if ctx.guild else 'N/A'})"
            )
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, commands.CommandOnCooldown):
            logger.info(
                f"Command {ctx.command} on cooldown for {ctx.author} ({ctx.author.id}), retry after {error.retry_after:.1f}s"
            )
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, commands.NoPrivateMessage):
            logger.warning(
                f"Guild-only command {ctx.command} attempted in DM by {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, commands.PrivateMessageOnly):
            logger.warning(
                f"DM-only command {ctx.command} attempted in guild {ctx.guild.name if ctx.guild else 'unknown'} by {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.dm_only_embed()

        elif isinstance(error, commands.DisabledCommand):
            logger.info(
                f"Disabled command {ctx.command} attempted by {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.error_embed(
                "Befehl deaktiviert", "Dieser Befehl ist derzeit deaktiviert."
            )

        elif isinstance(error, commands.NotOwner):
            logger.warning(
                f"Owner-only command {ctx.command} attempted by non-owner {ctx.author} ({ctx.author.id})"
            )
            embed = EmbedFactory.error_embed(
                "Berechtigung verweigert",
                "Nur der Bot-Besitzer kann diesen Befehl verwenden.",
            )

        elif isinstance(error, commands.CheckFailure):
            logger.warning(
                f"Check failure for command {ctx.command} by {ctx.author} ({ctx.author.id}): {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Überprüfung fehlgeschlagen",
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl.",
            )

        elif isinstance(error, discord.HTTPException):
            logger.error(
                f"HTTP exception in command {ctx.command} by {ctx.author} ({ctx.author.id}): {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Befehlsausführung")
            logger.error(
                f"Unbehandelter Fehler: {type(error).__name__}: {error}", exc_info=error
            )

        # Sende Error-Embed
        if embed:
            try:
                # Versuche ephemeral für Slash Commands
                if ctx.interaction and not ctx.interaction.response.is_done():
                    await ctx.interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
                elif ctx.interaction and ctx.interaction.response.is_done():
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.send(embed=embed)
            except Exception as send_error:
                logger.error(f"Fehler beim Senden der Fehlermeldung: {send_error}")

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        """Globaler Error Handler für Slash Commands"""
        # Log den Fehler für Debugging (ohne full traceback für bekannte Fehler)
        if isinstance(
            error,
            (
                discord.app_commands.CommandNotFound,
                discord.app_commands.MissingPermissions,
                discord.app_commands.BotMissingPermissions,
                discord.app_commands.CommandOnCooldown,
                discord.app_commands.NoPrivateMessage,
                discord.app_commands.CheckFailure,
                discord.HTTPException,
            ),
        ):
            # Für bekannte Fehler nur basic logging ohne traceback
            pass
        else:
            # Für unbekannte Fehler full logging mit traceback
            logger.error(
                f"App command error in {interaction.command}: {type(error).__name__}: {error}",
                exc_info=error,
            )

        embed = None

        # Spezifische Fehlerbehandlung für App Commands
        if isinstance(error, discord.app_commands.CommandNotFound):
            command_name = "unbekannt"
            if interaction.data and "name" in interaction.data:
                command_name = interaction.data["name"]
            logger.info(
                f"App command not found: '{command_name}' by {interaction.user} ({interaction.user.id}) in {interaction.guild.name if interaction.guild else 'DM'}"
            )
            embed = EmbedFactory.command_not_found_embed(command_name)

        elif isinstance(error, discord.app_commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.warning(
                f"Missing permissions ({missing_perms}) for app command {interaction.command} by {interaction.user} ({interaction.user.id}) in {interaction.guild.name if interaction.guild else 'DM'}"
            )
            embed = EmbedFactory.missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            logger.error(
                f"Bot missing permissions ({missing_perms}) for app command {interaction.command} in {interaction.guild.name if interaction.guild else 'DM'} (Guild ID: {interaction.guild.id if interaction.guild else 'N/A'})"
            )
            embed = EmbedFactory.bot_missing_permissions_embed(missing_perms)

        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            logger.info(
                f"App command {interaction.command} on cooldown for {interaction.user} ({interaction.user.id}), retry after {error.retry_after:.1f}s"
            )
            embed = EmbedFactory.cooldown_embed(error.retry_after)

        elif isinstance(error, discord.app_commands.NoPrivateMessage):
            logger.warning(
                f"Guild-only app command {interaction.command} attempted in DM by {interaction.user} ({interaction.user.id})"
            )
            embed = EmbedFactory.guild_only_embed()

        elif isinstance(error, discord.app_commands.CheckFailure):
            logger.warning(
                f"Check failure for app command {interaction.command} by {interaction.user} ({interaction.user.id}): {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Überprüfung fehlgeschlagen",
                "Du erfüllst nicht die Voraussetzungen für diesen Befehl.",
            )

        elif isinstance(error, discord.HTTPException):
            logger.error(
                f"HTTP exception in app command {interaction.command} by {interaction.user} ({interaction.user.id}): {str(error)}"
            )
            embed = EmbedFactory.error_embed(
                "Discord API Fehler",
                "Es gab ein Problem bei der Kommunikation mit Discord. Versuche es später erneut.",
            )

        else:
            # Unbekannte Fehler
            embed = EmbedFactory.unexpected_error_embed("Slash-Befehlsausführung")
            logger.error(
                f"Unbehandelter App Command Fehler: {type(error).__name__}: {error}",
                exc_info=error,
            )

        # Sende Error-Embed
        if embed:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as send_error:
                logger.error(
                    f"Fehler beim Senden der App Command Fehlermeldung: {send_error}"
                )


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

        # frame parameter is required for signal handlers but not used
        _ = frame

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
