"""
Konfigurationskommandos für Servereinstellungen
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import EmbedFactory
from utils.logging import log_command_error
from utils.responses import send_error_response

# Constants
CONFIG_TIMEOUT = 300
MIN_VALUES = 1
MAX_VALUES = 1
MAX_SELECT_OPTIONS = 24  # Discord limit is 25 options
MAX_PREFIX_LENGTH = 5

logger = logging.getLogger(__name__)


class ConfigOptionSelect(discord.ui.Select):
    """Select-Menü für Konfigurationsoptionen"""

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Konfiguration anzeigen",
                value="show",
                description="Zeigt die aktuelle Serverkonfiguration an",
            ),
            discord.SelectOption(
                label="Command-Prefix ändern",
                value="prefix",
                description="Ändert den Command-Prefix für den Server",
            ),
            discord.SelectOption(
                label="Log-Kanal setzen",
                value="logchannel",
                description="Setzt oder entfernt den Log-Kanal",
            ),
            discord.SelectOption(
                label="News-Kanal setzen",
                value="newschannel",
                description="Setzt oder entfernt den News-Kanal",
            ),
            discord.SelectOption(
                label="Nur-Bild-Kanal hinzufügen",
                value="add_pic_channel",
                description="Fügt einen Nur-Bild-Kanal hinzu",
            ),
            discord.SelectOption(
                label="Nur-Bild-Kanal entfernen",
                value="remove_pic_channel",
                description="Entfernt einen Nur-Bild-Kanal",
            ),
            discord.SelectOption(
                label="Geburtstags-Kanal hinzufügen",
                value="add_birthday_channel",
                description="Fügt einen Geburtstags-Benachrichtigungskanal hinzu",
            ),
            discord.SelectOption(
                label="Geburtstags-Kanal entfernen",
                value="remove_birthday_channel",
                description="Entfernt einen Geburtstags-Benachrichtigungskanal",
            ),
        ]

        super().__init__(
            placeholder="Wähle eine Konfigurationsoption...",
            min_values=MIN_VALUES,
            max_values=MAX_VALUES,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        from discord.ext.commands import Bot

        if not isinstance(interaction.client, Bot):
            return
        cog = interaction.client.get_cog("ConfigCog")
        if not cog or not isinstance(cog, ConfigCog):
            return

        selected_option = self.values[0]

        if selected_option == "show":
            await cog.handle_show_config(interaction)
        else:
            await cog.handle_config_option_selected(interaction, selected_option)


class ConfigOptionView(discord.ui.View):
    """View für Konfigurationsoptionen"""

    def __init__(self):
        super().__init__(timeout=CONFIG_TIMEOUT)
        self.add_item(ConfigOptionSelect())


class PrefixSelect(discord.ui.Select):
    """Select-Menü für Prefix-Optionen"""

    def __init__(self):
        options = [
            discord.SelectOption(label="!", value="!", description="Standard Prefix"),
            discord.SelectOption(label="?", value="?", description="Frage-Prefix"),
            discord.SelectOption(label=".", value=".", description="Punkt-Prefix"),
            discord.SelectOption(label=">", value=">", description="Pfeil-Prefix"),
            discord.SelectOption(
                label="Benutzerdefinierten Prefix eingeben",
                value="custom",
                description="Gib einen eigenen Prefix ein",
            ),
        ]

        super().__init__(
            placeholder="Wähle einen neuen Prefix...",
            min_values=MIN_VALUES,
            max_values=MAX_VALUES,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        from discord.ext.commands import Bot

        if not isinstance(interaction.client, Bot):
            return
        cog = interaction.client.get_cog("ConfigCog")
        if not cog or not isinstance(cog, ConfigCog):
            return

        selected_prefix = self.values[0]

        if selected_prefix == "custom":
            await cog.show_custom_prefix_modal(interaction)
        else:
            await cog.set_prefix_value(interaction, selected_prefix)


class PrefixView(discord.ui.View):
    """View für Prefix-Auswahl"""

    def __init__(self):
        super().__init__(timeout=CONFIG_TIMEOUT)
        self.add_item(PrefixSelect())


class ChannelSelect(discord.ui.Select):
    """Select-Menü für Kanal-Auswahl"""

    def __init__(self, channels, config_type, allow_none=False):
        options = []

        if allow_none:
            options.append(
                discord.SelectOption(
                    label="Entfernen/Deaktivieren",
                    value="none",
                    description="Entfernt die aktuelle Einstellung",
                )
            )

        for channel in channels[:MAX_SELECT_OPTIONS]:  # Discord limit is 25 options
            options.append(
                discord.SelectOption(
                    label=f"#{channel.name}",
                    value=str(channel.id),
                    description=f"Kanal: {channel.name}",
                )
            )

        super().__init__(
            placeholder="Wähle einen Kanal...",
            min_values=MIN_VALUES,
            max_values=MAX_VALUES,
            options=options,
        )

        self.config_type = config_type

    async def callback(self, interaction: discord.Interaction):
        from discord.ext.commands import Bot

        if not isinstance(interaction.client, Bot):
            return
        cog = interaction.client.get_cog("ConfigCog")
        if not cog or not isinstance(cog, ConfigCog):
            return

        selected_value = self.values[0]

        if selected_value == "none":
            channel_id = None
        else:
            channel_id = int(selected_value)

        await cog.set_channel_value(interaction, self.config_type, channel_id)


class ChannelView(discord.ui.View):
    """View für Kanal-Auswahl"""

    def __init__(self, channels, config_type, allow_none=False):
        super().__init__(timeout=CONFIG_TIMEOUT)
        self.add_item(ChannelSelect(channels, config_type, allow_none))


class CustomPrefixModal(discord.ui.Modal):
    """Modal für benutzerdefinierten Prefix"""

    def __init__(self):
        super().__init__(title="Benutzerdefinierten Prefix eingeben")

        self.prefix_input = discord.ui.TextInput(
            label="Neuer Prefix",
            placeholder="Gib deinen gewünschten Prefix ein...",
            max_length=MAX_PREFIX_LENGTH,
            min_length=MIN_VALUES,
        )
        self.add_item(self.prefix_input)

    async def on_submit(self, interaction: discord.Interaction):
        from discord.ext.commands import Bot

        if not isinstance(interaction.client, Bot):
            return
        cog = interaction.client.get_cog("ConfigCog")
        if not cog or not isinstance(cog, ConfigCog):
            return

        new_prefix = self.prefix_input.value.strip()
        await cog.set_prefix_value(interaction, new_prefix)


class ConfigCog(commands.Cog):
    """Cog für Serverkonfiguration"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.command(
        name="config", description="Zeigt oder ändert die Serverkonfiguration"
    )
    async def config(self, interaction: discord.Interaction):
        """Haupt-Konfigurationskommando"""

        embed = EmbedFactory.info_embed(
            title="Serverkonfiguration",
            description="Wähle eine Konfigurationsoption aus dem Menü unten:",
        )

        view = ConfigOptionView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_show_config(self, interaction: discord.Interaction):
        """Behandelt die Anzeige der Konfiguration"""
        if not interaction.guild:
            return

        try:
            guild_id = interaction.guild.id
            config = await self.bot.db.get_guild_config(guild_id)
            await self._show_config(interaction, config)
        except Exception as e:
            log_command_error(
                logger, "config-show", interaction.user, interaction.guild, e
            )
            await send_error_response(
                interaction,
                "Fehler",
                "Es ist ein Fehler beim Laden der Konfiguration aufgetreten.",
                ephemeral=True,
            )

    async def handle_config_option_selected(
        self, interaction: discord.Interaction, option: str
    ):
        """Behandelt die Auswahl einer Konfigurationsoption"""
        if not interaction.guild:
            return

        try:
            if option == "prefix":
                embed = EmbedFactory.info_embed(
                    title="Prefix ändern",
                    description="Wähle einen neuen Command-Prefix:",
                )
                view = PrefixView()
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "logchannel":
                channels = [
                    ch
                    for ch in interaction.guild.text_channels
                    if ch.permissions_for(interaction.guild.me).send_messages
                ]
                if not channels:
                    await send_error_response(
                        interaction,
                        "Keine Kanäle verfügbar",
                        "Es wurden keine Textkanäle gefunden, in die ich schreiben kann.",
                        ephemeral=True,
                    )
                    return

                embed = EmbedFactory.info_embed(
                    title="Log-Kanal setzen",
                    description="Wähle einen Kanal für die Log-Nachrichten:",
                )
                view = ChannelView(channels, "logchannel", allow_none=True)
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "newschannel":
                channels = [
                    ch
                    for ch in interaction.guild.text_channels
                    if ch.permissions_for(interaction.guild.me).send_messages
                ]
                if not channels:
                    await send_error_response(
                        interaction,
                        "Keine Kanäle verfügbar",
                        "Es wurden keine Textkanäle gefunden, in die ich schreiben kann.",
                        ephemeral=True,
                    )
                    return

                embed = EmbedFactory.info_embed(
                    title="News-Kanal setzen",
                    description="Wähle einen Kanal für die News-Nachrichten:",
                )
                view = ChannelView(channels, "newschannel", allow_none=True)
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "add_pic_channel":
                channels = interaction.guild.text_channels
                if not channels:
                    await send_error_response(
                        interaction,
                        "Keine Kanäle verfügbar",
                        "Es wurden keine Textkanäle gefunden.",
                        ephemeral=True,
                    )
                    return

                embed = EmbedFactory.info_embed(
                    title="Nur-Bild-Kanal hinzufügen",
                    description="Wähle einen Kanal, der als Nur-Bild-Kanal konfiguriert werden soll:",
                )
                view = ChannelView(channels, "add_pic_channel")
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "remove_pic_channel":
                try:
                    guild_id = interaction.guild.id
                    config = await self.bot.db.get_guild_config(guild_id)
                except Exception as e:
                    logger.error(
                        f"Fehler beim Laden der Konfiguration für remove_pic_channel: {e}"
                    )
                    embed = discord.Embed(
                        title="Datenbankfehler",
                        description="Die Konfiguration konnte nicht geladen werden.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                if not config.picture_only_channels:
                    embed = discord.Embed(
                        title="Keine Nur-Bild-Kanäle",
                        description="Es sind keine Nur-Bild-Kanäle konfiguriert.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Nur die konfigurierten Kanäle anzeigen
                configured_channels = []
                for channel_id in config.picture_only_channels:
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        configured_channels.append(channel)

                if not configured_channels:
                    embed = discord.Embed(
                        title="Keine gültigen Kanäle",
                        description="Alle konfigurierten Nur-Bild-Kanäle sind nicht mehr verfügbar.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                embed = discord.Embed(
                    title="Nur-Bild-Kanal entfernen",
                    description="Wähle einen Kanal, der aus den Nur-Bild-Kanälen entfernt werden soll:",
                    color=discord.Color.blurple(),
                )
                view = ChannelView(configured_channels, "remove_pic_channel")
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "add_birthday_channel":
                channels = [
                    ch
                    for ch in interaction.guild.text_channels
                    if ch.permissions_for(interaction.guild.me).send_messages
                ]
                if not channels:
                    embed = discord.Embed(
                        title="Keine Kanäle verfügbar",
                        description="Es wurden keine Textkanäle gefunden, in die ich schreiben kann.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                embed = discord.Embed(
                    title="Geburtstags-Kanal hinzufügen",
                    description="Wähle einen Kanal für Geburtstags-Benachrichtigungen:",
                    color=discord.Color.blurple(),
                )
                view = ChannelView(channels, "add_birthday_channel")
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )

            elif option == "remove_birthday_channel":
                try:
                    guild_id = interaction.guild.id
                    birthday_channel_id = await self.bot.db.get_birthday_channel(
                        guild_id
                    )
                except Exception as e:
                    logger.error(f"Fehler beim Laden des Geburtstags-Kanals: {e}")
                    embed = discord.Embed(
                        title="Datenbankfehler",
                        description="Der Geburtstags-Kanal konnte nicht geladen werden.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                if not birthday_channel_id:
                    embed = discord.Embed(
                        title="Kein Geburtstags-Kanal",
                        description="Es ist kein Geburtstags-Kanal konfiguriert.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Direkt entfernen da nur ein Kanal konfiguriert ist
                success = await self.bot.db.remove_birthday_channel(guild_id)

                if success:
                    channel = interaction.guild.get_channel(birthday_channel_id)
                    channel_name = (
                        channel.mention if channel else f"<#{birthday_channel_id}>"
                    )
                    embed = discord.Embed(
                        title="Geburtstags-Kanal entfernt",
                        description=f"{channel_name} wurde aus den Geburtstags-Benachrichtigungen entfernt.",
                        color=discord.Color.green(),
                    )
                else:
                    embed = discord.Embed(
                        title="Fehler",
                        description="Der Geburtstags-Kanal konnte nicht entfernt werden.",
                        color=discord.Color.red(),
                    )

                await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler bei Konfigurationsoption {option}: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Verarbeiten der Konfiguration aufgetreten.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_custom_prefix_modal(self, interaction: discord.Interaction):
        """Zeigt das Modal für benutzerdefinierten Prefix"""
        modal = CustomPrefixModal()
        await interaction.response.send_modal(modal)

    async def set_prefix_value(self, interaction: discord.Interaction, new_prefix: str):
        """Setzt einen neuen Prefix-Wert"""
        if not interaction.guild:
            return

        try:
            guild_id = interaction.guild.id
            config = await self.bot.db.get_guild_config(guild_id)
            await self._set_prefix_direct(interaction, config, new_prefix)
        except Exception as e:
            logger.error(f"Fehler beim Setzen des Prefix: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Setzen des Prefix aufgetreten.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def set_channel_value(
        self,
        interaction: discord.Interaction,
        config_type: str,
        channel_id: Optional[int],
    ):
        """Setzt einen Kanal-Wert"""
        if not interaction.guild:
            return

        try:
            guild_id = interaction.guild.id
            config = await self.bot.db.get_guild_config(guild_id)

            if config_type == "logchannel":
                await self._set_log_channel_direct(interaction, config, channel_id)
            elif config_type == "newschannel":
                await self._set_news_channel_direct(interaction, config, channel_id)
            elif config_type == "add_pic_channel" and channel_id is not None:
                await self._add_picture_channel_direct(interaction, config, channel_id)
            elif config_type == "remove_pic_channel" and channel_id is not None:
                await self._remove_picture_channel_direct(
                    interaction, config, channel_id
                )
            elif config_type == "add_birthday_channel" and channel_id is not None:
                await self._add_birthday_channel_direct(interaction, channel_id)
            elif config_type == "remove_birthday_channel":
                # Für remove_birthday_channel ignorieren wir channel_id da nur ein Kanal gesetzt werden kann
                await self._remove_birthday_channel_direct(interaction)

        except Exception as e:
            logger.error(f"Fehler beim Setzen des Kanals ({config_type}): {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Setzen des Kanals aufgetreten.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _set_prefix_direct(
        self, interaction: discord.Interaction, config, new_prefix: str
    ):
        """Setzt einen neuen Command-Prefix direkt"""
        if len(new_prefix) > MAX_PREFIX_LENGTH:
            embed = discord.Embed(
                title="Prefix zu lang",
                description=f"Der Prefix darf maximal {MAX_PREFIX_LENGTH} Zeichen lang sein.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        old_prefix = config.command_prefix
        success = await self.bot.db.set_command_prefix(config.guild_id, new_prefix)

        if success:
            embed = discord.Embed(
                title="Prefix geändert",
                description=f"Command-Prefix wurde von `{old_prefix}` zu `{new_prefix}` geändert.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der Prefix konnte nicht geändert werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _set_log_channel_direct(
        self, interaction: discord.Interaction, config, channel_id: Optional[int]
    ):
        """Setzt den Log-Kanal direkt"""
        if not interaction.guild:
            return

        if channel_id is None:
            # Entferne Log-Kanal
            success = await self.bot.db.set_log_channel(config.guild_id, None)

            if success:
                embed = discord.Embed(
                    title="Log-Kanal entfernt",
                    description="Der Log-Kanal wurde deaktiviert.",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Der Log-Kanal konnte nicht entfernt werden.",
                    color=discord.Color.red(),
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = await self.bot.db.set_log_channel(config.guild_id, channel.id)

        if success:
            embed = discord.Embed(
                title="Log-Kanal gesetzt",
                description=f"Log-Kanal wurde auf {channel.mention} gesetzt.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der Log-Kanal konnte nicht gesetzt werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _set_news_channel_direct(
        self, interaction: discord.Interaction, config, channel_id: Optional[int]
    ):
        """Setzt den News-Kanal direkt"""
        if not interaction.guild:
            return

        if channel_id is None:
            # Entferne News-Kanal
            success = await self.bot.db.set_news_channel(config.guild_id, None)

            if success:
                embed = discord.Embed(
                    title="News-Kanal entfernt",
                    description="Der News-Kanal wurde deaktiviert.",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Der News-Kanal konnte nicht entfernt werden.",
                    color=discord.Color.red(),
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = await self.bot.db.set_news_channel(config.guild_id, channel.id)

        if success:
            embed = discord.Embed(
                title="News-Kanal gesetzt",
                description=f"News-Kanal wurde auf {channel.mention} gesetzt.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der News-Kanal konnte nicht gesetzt werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _add_picture_channel_direct(
        self, interaction: discord.Interaction, config, channel_id: int
    ):
        """Fügt einen Nur-Bild-Kanal direkt hinzu"""
        if not interaction.guild:
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prüfe ob Kanal bereits konfiguriert ist
        if channel.id in config.picture_only_channels:
            embed = discord.Embed(
                title="Bereits konfiguriert",
                description=f"{channel.mention} ist bereits als Nur-Bild-Kanal konfiguriert.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = await self.bot.db.add_picture_only_channel(
            config.guild_id, channel.id
        )

        if success:
            embed = discord.Embed(
                title="Nur-Bild-Kanal hinzugefügt",
                description=f"{channel.mention} wurde als Nur-Bild-Kanal konfiguriert.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der Nur-Bild-Kanal konnte nicht hinzugefügt werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _remove_picture_channel_direct(
        self, interaction: discord.Interaction, config, channel_id: int
    ):
        """Entfernt einen Nur-Bild-Kanal direkt"""
        if not interaction.guild:
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prüfe ob Kanal konfiguriert ist
        if channel.id not in config.picture_only_channels:
            embed = discord.Embed(
                title="Nicht konfiguriert",
                description=f"{channel.mention} ist nicht als Nur-Bild-Kanal konfiguriert.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = await self.bot.db.remove_picture_only_channel(
            config.guild_id, channel.id
        )

        if success:
            embed = discord.Embed(
                title="Nur-Bild-Kanal entfernt",
                description=f"{channel.mention} wurde aus den Nur-Bild-Kanälen entfernt.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der Nur-Bild-Kanal konnte nicht entfernt werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _add_birthday_channel_direct(
        self, interaction: discord.Interaction, channel_id: int
    ):
        """Fügt einen Geburtstags-Kanal direkt hinzu"""
        if not interaction.guild:
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prüfe ob bereits ein Kanal konfiguriert ist
        existing_channel_id = await self.bot.db.get_birthday_channel(
            interaction.guild.id
        )

        if existing_channel_id == channel.id:
            embed = discord.Embed(
                title="Bereits konfiguriert",
                description=f"{channel.mention} ist bereits als Geburtstags-Kanal konfiguriert.",
                color=discord.Color.orange(),
            )
        else:
            success = await self.bot.db.add_birthday_channel(
                interaction.guild.id, channel.id
            )

            if success:
                if existing_channel_id:
                    old_channel = interaction.guild.get_channel(existing_channel_id)
                    old_channel_name = (
                        old_channel.mention
                        if old_channel
                        else f"<#{existing_channel_id}>"
                    )
                    embed = discord.Embed(
                        title="Geburtstags-Kanal aktualisiert",
                        description=f"Geburtstags-Benachrichtigungen werden jetzt in {channel.mention} gesendet (vorher: {old_channel_name}).",
                        color=discord.Color.green(),
                    )
                else:
                    embed = discord.Embed(
                        title="Geburtstags-Kanal hinzugefügt",
                        description=f"{channel.mention} wurde als Geburtstags-Benachrichtigungskanal konfiguriert.",
                        color=discord.Color.green(),
                    )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Der Geburtstags-Kanal konnte nicht konfiguriert werden.",
                    color=discord.Color.red(),
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _remove_birthday_channel_direct(self, interaction: discord.Interaction):
        """Entfernt den Geburtstags-Kanal direkt"""
        if not interaction.guild:
            return

        # Hole den aktuell konfigurierten Kanal
        birthday_channel_id = await self.bot.db.get_birthday_channel(
            interaction.guild.id
        )
        if not birthday_channel_id:
            embed = discord.Embed(
                title="Kein Geburtstags-Kanal",
                description="Es ist kein Geburtstags-Kanal konfiguriert.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        success = await self.bot.db.remove_birthday_channel(interaction.guild.id)

        if success:
            channel = interaction.guild.get_channel(birthday_channel_id)
            channel_name = channel.mention if channel else f"<#{birthday_channel_id}>"
            embed = discord.Embed(
                title="Geburtstags-Kanal entfernt",
                description=f"{channel_name} wurde aus den Geburtstags-Benachrichtigungen entfernt.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="Fehler",
                description="Der Geburtstags-Kanal konnte nicht entfernt werden.",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _show_config(self, interaction: discord.Interaction, config):
        """Zeigt die aktuelle Konfiguration an"""

        if not interaction.guild:
            return

        # Log-Kanal anzeigen
        log_channel_text = "Nicht konfiguriert"
        if config.log_channel_id:
            log_channel = interaction.guild.get_channel(config.log_channel_id)
            if log_channel:
                log_channel_text = f"#{log_channel.name}"
            else:
                log_channel_text = f"Kanal nicht gefunden (ID: {config.log_channel_id})"

        # News-Kanal anzeigen
        news_channel_text = "Nicht konfiguriert"
        if config.news_channel_id:
            news_channel = interaction.guild.get_channel(config.news_channel_id)
            if news_channel:
                news_channel_text = f"#{news_channel.name}"
            else:
                news_channel_text = (
                    f"Kanal nicht gefunden (ID: {config.news_channel_id})"
                )

        # Bild-Kanäle anzeigen
        pic_channels_text = "Keine konfiguriert"
        if config.picture_only_channels:
            pic_channel_names = []
            for channel_id in config.picture_only_channels:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    pic_channel_names.append(f"#{channel.name}")
                else:
                    pic_channel_names.append(f"Unbekannt (ID: {channel_id})")
            pic_channels_text = ", ".join(pic_channel_names)

        # Geburtstags-Kanal anzeigen
        birthday_channel_text = "Nicht konfiguriert"
        try:
            birthday_channel_id = await self.bot.db.get_birthday_channel(
                interaction.guild.id
            )
            if birthday_channel_id:
                channel = interaction.guild.get_channel(birthday_channel_id)
                if channel:
                    birthday_channel_text = f"#{channel.name}"
                else:
                    birthday_channel_text = f"Unbekannt (ID: {birthday_channel_id})"
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Geburtstags-Kanals für Anzeige: {e}")
            birthday_channel_text = "Fehler beim Laden"

        embed = discord.Embed(
            title="Serverkonfiguration",
            description=f"Konfiguration für **{interaction.guild.name}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Command-Prefix", value=f"`{config.command_prefix}`", inline=True
        )
        embed.add_field(name="Log-Kanal", value=log_channel_text, inline=True)
        embed.add_field(name="News-Kanal", value=news_channel_text, inline=True)
        embed.add_field(name="Nur-Bild-Kanäle", value=pic_channels_text, inline=False)
        embed.add_field(
            name="Geburtstags-Kanal", value=birthday_channel_text, inline=False
        )
        embed.set_footer(text="Verwende /config um Einstellungen zu ändern")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
