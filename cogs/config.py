"""
Konfigurationskommandos für Servereinstellungen
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class ConfigCog(commands.Cog):
    """Cog für Serverkonfiguration"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="config", description="Zeigt oder ändert die Serverkonfiguration"
    )
    @app_commands.describe(
        aktion="Die gewünschte Aktion (anzeigen, prefix, logkanal, bild-channel)",
        wert="Der neue Wert für die Konfiguration",
    )
    @app_commands.choices(
        aktion=[
            app_commands.Choice(name="anzeigen", value="show"),
            app_commands.Choice(name="prefix", value="prefix"),
            app_commands.Choice(name="logkanal", value="logchannel"),
            app_commands.Choice(
                name="bild-channel-hinzufügen", value="add_pic_channel"
            ),
            app_commands.Choice(
                name="bild-channel-entfernen", value="remove_pic_channel"
            ),
        ]
    )
    async def config(
        self,
        interaction: discord.Interaction,
        aktion: app_commands.Choice[str],
        wert: Optional[str] = None,
    ):
        """Haupt-Konfigurationskommando"""

        # Überprüfe Administrator-Berechtigung
        if not interaction.guild:
            embed = discord.Embed(
                title="Fehler",
                description="Dieser Befehl kann nur in einem Server verwendet werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Hole Member Objekt für Berechtigungen
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.guild_permissions.administrator:
            embed = discord.Embed(
                title="Keine Berechtigung",
                description="Du benötigst Administrator-Rechte, um die Serverkonfiguration zu ändern.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild.id

        try:
            config = await self.bot.db.get_server_config(guild_id)

            if aktion.value == "show":
                await self._show_config(interaction, config)
            elif aktion.value == "prefix":
                await self._set_prefix(interaction, config, wert)
            elif aktion.value == "logchannel":
                await self._set_log_channel(interaction, config, wert)
            elif aktion.value == "add_pic_channel":
                await self._add_picture_channel(interaction, config, wert)
            elif aktion.value == "remove_pic_channel":
                await self._remove_picture_channel(interaction, config, wert)

        except Exception as e:
            logger.error(f"Fehler bei Konfigurationskommando: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Verarbeiten der Konfiguration aufgetreten.",
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

        embed = discord.Embed(
            title="Serverkonfiguration",
            description=f"Konfiguration für **{interaction.guild.name}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Command-Prefix", value=f"`{config.command_prefix}`", inline=True
        )
        embed.add_field(name="Log-Kanal", value=log_channel_text, inline=True)
        embed.add_field(name="Nur-Bild-Kanäle", value=pic_channels_text, inline=False)
        embed.set_footer(text="Verwende /config um Einstellungen zu ändern")

        await interaction.response.send_message(embed=embed)

    async def _set_prefix(
        self, interaction: discord.Interaction, config, new_prefix: Optional[str]
    ):
        """Setzt einen neuen Command-Prefix"""

        if not new_prefix:
            embed = discord.Embed(
                title="Ungültiger Prefix",
                description="Bitte gib einen gültigen Prefix an.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(new_prefix) > 5:
            embed = discord.Embed(
                title="Prefix zu lang",
                description="Der Prefix darf maximal 5 Zeichen lang sein.",
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

        await interaction.response.send_message(embed=embed)

    async def _set_log_channel(
        self, interaction: discord.Interaction, config, channel_mention: Optional[str]
    ):
        """Setzt den Log-Kanal"""

        if not interaction.guild:
            return

        if not channel_mention:
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

            await interaction.response.send_message(embed=embed)
            return

        # Versuche Channel-ID zu extrahieren
        channel = None

        # Prüfe ob es eine Channel-Mention ist
        if channel_mention.startswith("<#") and channel_mention.endswith(">"):
            try:
                channel_id = int(channel_mention[2:-1])
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass
        # Prüfe ob es eine reine ID ist
        elif channel_mention.isdigit():
            try:
                channel_id = int(channel_mention)
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass

        if not channel:
            embed = discord.Embed(
                title="Kanal nicht gefunden",
                description="Der angegebene Kanal konnte nicht gefunden werden. Verwende eine Channel-Mention (#kanal) oder eine Kanal-ID.",
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

        await interaction.response.send_message(embed=embed)

    async def _add_picture_channel(
        self, interaction: discord.Interaction, config, channel_mention: Optional[str]
    ):
        """Fügt einen Nur-Bild-Kanal hinzu"""

        if not interaction.guild:
            return

        if not channel_mention:
            embed = discord.Embed(
                title="Kanal erforderlich",
                description="Bitte gib einen Kanal an, der als Nur-Bild-Kanal konfiguriert werden soll.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Versuche Channel-ID zu extrahieren
        channel = None

        if channel_mention.startswith("<#") and channel_mention.endswith(">"):
            try:
                channel_id = int(channel_mention[2:-1])
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass
        elif channel_mention.isdigit():
            try:
                channel_id = int(channel_mention)
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass

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

        await interaction.response.send_message(embed=embed)

    async def _remove_picture_channel(
        self, interaction: discord.Interaction, config, channel_mention: Optional[str]
    ):
        """Entfernt einen Nur-Bild-Kanal"""

        if not interaction.guild:
            return

        if not channel_mention:
            embed = discord.Embed(
                title="Kanal erforderlich",
                description="Bitte gib einen Kanal an, der aus den Nur-Bild-Kanälen entfernt werden soll.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Versuche Channel-ID zu extrahieren
        channel = None

        if channel_mention.startswith("<#") and channel_mention.endswith(">"):
            try:
                channel_id = int(channel_mention[2:-1])
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass
        elif channel_mention.isdigit():
            try:
                channel_id = int(channel_mention)
                channel = interaction.guild.get_channel(channel_id)
            except ValueError:
                pass

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

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
