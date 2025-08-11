"""
General utilities package
Contains utilities that are not specific to the Discord bot
"""

# General constants that can be used across the application
from .constants import GERMAN_MONTH_NAMES, HARDWARE_KEYWORDS

# General formatting utilities
from .formatting import (
    format_channel_info,
    format_command_context,
    format_file_size,
    format_guild_info,
    format_member_status,
    format_permission_list,
    format_timestamp,
    format_user_info,
    truncate_text,
)

# Logging utilities
from .logging import (
    ColoredConsoleHandler,
    log_api_request,
    log_command_error,
    log_command_execution,
    log_command_success,
    log_database_operation,
    setup_logging,
)

__all__ = [
    "GERMAN_MONTH_NAMES",
    "HARDWARE_KEYWORDS",
    "format_guild_info",
    "format_user_info",
    "format_channel_info",
    "format_command_context",
    "format_permission_list",
    "format_member_status",
    "truncate_text",
    "format_timestamp",
    "format_file_size",
    "setup_logging",
    "log_command_execution",
    "log_command_success",
    "log_command_error",
    "log_database_operation",
    "log_api_request",
    "ColoredConsoleHandler",
]
