"""
Database utility functions for server configuration management.
"""

import aiosqlite
import json
import logging
from typing import Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Data class for server configuration."""

    guild_id: int
    command_prefix: str = "!"
    log_channel_id: Optional[int] = None
    picture_only_channels: List[int] = field(default_factory=list)


class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get_server_config(self, guild_id: int) -> ServerConfig:
        """
        Get server configuration for a guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            ServerConfig object with the guild's configuration
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, picture_only_channels "
                    "FROM server_config WHERE guild_id = ?",
                    (guild_id,),
                )
                row = await cursor.fetchone()

                if row:
                    picture_only_channels = json.loads(row[3]) if row[3] else []
                    return ServerConfig(
                        guild_id=row[0],
                        command_prefix=row[1],
                        log_channel_id=row[2],
                        picture_only_channels=picture_only_channels,
                    )
                else:
                    # Return default configuration for new guilds
                    return ServerConfig(guild_id=guild_id)

        except Exception as e:
            logger.error(f"Error getting server config for guild {guild_id}: {e}")
            # Return default configuration on error
            return ServerConfig(guild_id=guild_id)

    async def set_server_config(self, config: ServerConfig) -> bool:
        """
        Set server configuration for a guild.

        Args:
            config: ServerConfig object with the new configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            picture_only_json = json.dumps(config.picture_only_channels)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO server_config 
                       (guild_id, command_prefix, log_channel_id, picture_only_channels)
                       VALUES (?, ?, ?, ?)""",
                    (
                        config.guild_id,
                        config.command_prefix,
                        config.log_channel_id,
                        picture_only_json,
                    ),
                )
                await db.commit()

            logger.info(f"Updated server config for guild {config.guild_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error setting server config for guild {config.guild_id}: {e}"
            )
            return False

    async def set_command_prefix(self, guild_id: int, prefix: str) -> bool:
        """
        Set command prefix for a guild.

        Args:
            guild_id: Discord guild ID
            prefix: New command prefix

        Returns:
            True if successful, False otherwise
        """
        try:
            config = await self.get_server_config(guild_id)
            config.command_prefix = prefix
            return await self.set_server_config(config)

        except Exception as e:
            logger.error(f"Error setting command prefix for guild {guild_id}: {e}")
            return False

    async def set_log_channel(self, guild_id: int, channel_id: Optional[int]) -> bool:
        """
        Set log channel for a guild.

        Args:
            guild_id: Discord guild ID
            channel_id: Channel ID for logging, None to disable

        Returns:
            True if successful, False otherwise
        """
        try:
            config = await self.get_server_config(guild_id)
            config.log_channel_id = channel_id
            return await self.set_server_config(config)

        except Exception as e:
            logger.error(f"Error setting log channel for guild {guild_id}: {e}")
            return False

    async def add_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Add a channel to the picture-only channels list.

        Args:
            guild_id: Discord guild ID
            channel_id: Channel ID to add

        Returns:
            True if successful, False otherwise
        """
        try:
            config = await self.get_server_config(guild_id)
            if channel_id not in config.picture_only_channels:
                config.picture_only_channels.append(channel_id)
                return await self.set_server_config(config)
            return True

        except Exception as e:
            logger.error(f"Error adding picture-only channel for guild {guild_id}: {e}")
            return False

    async def remove_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Remove a channel from the picture-only channels list.

        Args:
            guild_id: Discord guild ID
            channel_id: Channel ID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            config = await self.get_server_config(guild_id)
            if channel_id in config.picture_only_channels:
                config.picture_only_channels.remove(channel_id)
                return await self.set_server_config(config)
            return True

        except Exception as e:
            logger.error(
                f"Error removing picture-only channel for guild {guild_id}: {e}"
            )
            return False

    async def is_picture_only_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Check if a channel is configured as picture-only.

        Args:
            guild_id: Discord guild ID
            channel_id: Channel ID to check

        Returns:
            True if channel is picture-only, False otherwise
        """
        try:
            config = await self.get_server_config(guild_id)
            return channel_id in config.picture_only_channels

        except Exception as e:
            logger.error(
                f"Error checking picture-only channel for guild {guild_id}: {e}"
            )
            return False

    async def get_all_server_configs(self) -> List[ServerConfig]:
        """
        Get all server configurations.

        Returns:
            List of ServerConfig objects
        """
        try:
            configs = []
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT guild_id, command_prefix, log_channel_id, picture_only_channels "
                    "FROM server_config"
                )
                rows = await cursor.fetchall()

                for row in rows:
                    picture_only_channels = json.loads(row[3]) if row[3] else []
                    configs.append(
                        ServerConfig(
                            guild_id=row[0],
                            command_prefix=row[1],
                            log_channel_id=row[2],
                            picture_only_channels=picture_only_channels,
                        )
                    )

            return configs

        except Exception as e:
            logger.error(f"Error getting all server configs: {e}")
            return []
