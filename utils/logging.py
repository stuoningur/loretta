"""
Logging-Konfiguration für den Loretta Discord Bot
Stellt farbige Console-Ausgabe und rotierende Datei-Handler bereit
"""

import logging
import logging.handlers
import os
from pathlib import Path


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
    Path("data").mkdir(exist_ok=True)

    # Erstelle Formattierer
    logging_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root-Logger-Setup
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # Entferne alle existierenden Handler

    # Datei-Handler mit Rotation (10MB max, behalte 5 Backup-Dateien)
    file_handler = logging.handlers.RotatingFileHandler(
        "data/loretta.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
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