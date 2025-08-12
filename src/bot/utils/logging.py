"""
Logging-Konfiguration für den Loretta Discord Bot
Stellt farbige Console-Ausgabe und rotierende Datei-Handler bereit
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Union

import discord

# Constants
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
BYTES_TO_GB_DIVISOR = 1024**3


class ColoredConsoleHandler(logging.StreamHandler):
    """Benutzerdefinierter Handler der Farbe zu Console-Output mit ANSI-Escape-Codes hinzufügt"""

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
    """Richtet Logging mit rotierenden Dateien und farbiger Console-Ausgabe ein"""
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())

    # Stelle sicher dass Daten-Verzeichnis existiert
    Path("logs").mkdir(exist_ok=True)

    # Erstelle Formattierer
    logging_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root-Logger-Setup
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # Entferne alle existierenden Handler

    # Datei-Handler mit Rotation
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/loretta.log",
        maxBytes=MAX_LOG_FILE_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging_formatter)
    file_handler.setLevel(log_level)

    # Farbiger Console-Handler
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(logging_formatter)
    console_handler.setLevel(log_level)

    # Füge Handler zu Root-Logger hinzu
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def log_command_execution(
    logger: logging.Logger,
    command_name: str,
    user: Union[discord.Member, discord.User],
    guild: Optional[discord.Guild],
    level: int = logging.INFO,
    **kwargs,
):
    """
    Loggt Command-Ausführung mit konsistenter Formatierung

    Args:
        logger: Logger-Instanz
        command_name: Name des ausgeführten Commands
        user: Benutzer der den Command ausführt
        guild: Guild wo der Command ausgeführt wird
        level: Log-Level (default: INFO)
        **kwargs: Zusätzliche Informationen für das Log
    """
    from utils.formatting import format_command_context

    message = format_command_context(command_name, user, guild, **kwargs)
    logger.log(level, message)


def log_command_success(
    logger: logging.Logger,
    command_name: str,
    user: Union[discord.Member, discord.User],
    guild: Optional[discord.Guild],
    **kwargs,
):
    """
    Loggt erfolgreiche Command-Ausführung
    """
    log_command_execution(logger, command_name, user, guild, logging.INFO, **kwargs)


def log_command_error(
    logger: logging.Logger,
    command_name: str,
    user: Union[discord.Member, discord.User],
    guild: Optional[discord.Guild],
    error: Exception,
    **kwargs,
):
    """
    Loggt Command-Fehler mit Exception-Informationen
    """
    from utils.formatting import format_command_context

    message = format_command_context(command_name, user, guild, **kwargs)
    logger.error(f"{message} - Fehler: {type(error).__name__}: {error}", exc_info=error)


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    guild_id: Optional[int] = None,
    user_id: Optional[int] = None,
    success: bool = True,
    error: Optional[Exception] = None,
):
    """
    Loggt Datenbank-Operationen konsistent

    Args:
        logger: Logger-Instanz
        operation: Beschreibung der Operation
        guild_id: Optional Guild-ID
        user_id: Optional Benutzer-ID
        success: Ob die Operation erfolgreich war
        error: Exception falls aufgetreten
    """
    context_parts = []
    if guild_id:
        context_parts.append(f"Guild:{guild_id}")
    if user_id:
        context_parts.append(f"User:{user_id}")

    context = f" ({', '.join(context_parts)})" if context_parts else ""

    if success:
        logger.info(f"Datenbank-Operation erfolgreich: {operation}{context}")
    else:
        error_msg = f": {error}" if error else ""
        logger.error(
            f"Datenbank-Operation fehlgeschlagen: {operation}{context}{error_msg}"
        )


def log_api_request(
    logger: logging.Logger,
    endpoint: str,
    status_code: Optional[int] = None,
    response_time: Optional[float] = None,
    error: Optional[Exception] = None,
):
    """
    Loggt API-Requests konsistent

    Args:
        logger: Logger-Instanz
        endpoint: API-Endpoint
        status_code: HTTP-Status-Code
        response_time: Antwortzeit in Sekunden
        error: Exception falls aufgetreten
    """
    if error:
        logger.error(f"API-Request fehlgeschlagen: {endpoint} - {error}")
    else:
        timing = f" ({response_time:.2f}s)" if response_time else ""
        status = f" [{status_code}]" if status_code else ""
        logger.info(f"API-Request: {endpoint}{status}{timing}")
