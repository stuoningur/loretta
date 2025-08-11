"""
Hilfe-Befehl für den Loretta Discord Bot
"""

import logging
from typing import Optional

from discord.ext import commands

from bot.utils.decorators import track_command_usage
from bot.utils.embeds import EmbedFactory

logger = logging.getLogger(__name__)


class Help(commands.Cog):
    """Hilfe-Befehl für Bot-Kommandos"""

    def __init__(self, bot):
        self.bot = bot
        # Entferne den Standard-Hilfe-Befehl
        self.bot.remove_command("help")

    @commands.hybrid_command(
        name="help",
        aliases=["hilfe"],
        description="Zeigt alle verfügbaren Bot-Befehle an",
    )
    @track_command_usage
    async def help(self, ctx, *, command_name: Optional[str] = None):
        """Zeigt Hilfe für Bot-Befehle an"""

        if command_name:
            # Zeige Hilfe für einen spezifischen Befehl
            await self._show_command_help(ctx, command_name)
        else:
            # Zeige allgemeine Hilfe
            await self._show_general_help(ctx)

    async def _show_general_help(self, ctx):
        """Zeigt die allgemeine Hilfe-Übersicht an"""

        embed = EmbedFactory.info_command_embed(
            title="Bot-Hilfe",
            description="Hier sind alle verfügbaren Befehle:",
            requester=ctx.author,
        )

        # Sammle alle verfügbaren Befehle basierend auf Benutzerberechtigungen
        available_commands = await self._get_available_commands(ctx)

        # Kategorien der Befehle (ohne Emojis) - mit korrekten Namen (alphabetisch sortiert)
        categories = {
            "Bot-Management": [
                "config",
                "listcogs",
                "load",
                "mystats",
                "purge",
                "reload",
                "reloadall",
                "shutdown",
                "stats",
                "sync",
                "unload",
            ],
            "Geburtstage": ["birthday_status", "birthday_test", "geburtstag"],
            "Hardware-Guides": [
                "anleitung",
                "bios",
                "cpu",
                "curve",
                "limit",
                "liste",
                "mainboard",
                "ramkit",
                "spd",
            ],
            "Hardware-Spezifikationen": ["specs"],
            "Suche & Informationen": [
                "computerbase_info",
                "computerbase_test",
                "hardwareluxx_info",
                "hardwareluxx_test",
                "hwbot",
                "pcgh_info",
                "pcgh_test",
                "screenshot",
                "software_info",
                "software_test",
                "weathershort",
                "wetter",
            ],
            "System & Info": ["botinfo", "ping", "serverinfo", "userinfo"],
            "Text-Tools": ["leetspeak", "schmutz", "sgehdn"],
            "Unterhaltung": [
                "8ball",
                "gif",
                "random",
                "roll",
                "why",
            ],
        }

        # Filtere und zeige nur verfügbare Befehle
        for category, command_names in categories.items():
            category_commands = []

            for cmd_name in command_names:
                if cmd_name in available_commands:
                    cmd = available_commands[cmd_name]
                    description = cmd.description or "Keine Beschreibung"
                    category_commands.append(f"`/{cmd_name}` - {description}")

            if category_commands:
                embed.add_field(
                    name=category, value="\n".join(category_commands), inline=False
                )

        embed.add_field(
            name="Tipp",
            value="Verwende `/help <Befehlsname>` für detaillierte Informationen zu einem Befehl.",
            inline=False,
        )

        await ctx.send(embed=embed)

    async def _get_available_commands(self, ctx):
        """Sammelt alle verfügbaren Befehle basierend auf Benutzerberechtigungen"""
        available_commands = {}

        # Sammle normale Bot-Befehle (hybrid und prefix commands)
        for command in self.bot.commands:
            try:
                # Prüfe ob der Benutzer den Befehl verwenden kann
                can_run = await command.can_run(ctx)
                if can_run:
                    available_commands[command.name] = command
                    # Füge auch Aliases hinzu
                    for alias in command.aliases:
                        available_commands[alias] = command
            except commands.CommandError:
                # Fallback: Verwende unser eigenes Permission-System
                if await self._check_command_permission(command.name, ctx):
                    available_commands[command.name] = command
                    # Füge auch Aliases hinzu
                    for alias in command.aliases:
                        available_commands[alias] = command

        # Sammle auch App-Commands (reine Slash-Commands) vom Command Tree mit Berechtigung-Prüfung
        try:
            if ctx.guild and ctx.author:
                # Guild-spezifische App-Commands
                for command in self.bot.tree.get_commands(guild=ctx.guild):
                    # Prüfe App-Command-Berechtigungen
                    if await self._can_use_app_command(command, ctx):
                        mock_command = type(
                            "MockCommand",
                            (),
                            {
                                "name": command.name,
                                "description": command.description,
                                "aliases": [],
                                "signature": "",
                                "help": command.description,
                            },
                        )()
                        available_commands[command.name] = mock_command

                # Globale App-Commands
                for command in self.bot.tree.get_commands():
                    if (
                        command.name not in available_commands
                    ):  # Vermeiden von Duplikaten
                        # Prüfe App-Command-Berechtigungen
                        if await self._can_use_app_command(command, ctx):
                            mock_command = type(
                                "MockCommand",
                                (),
                                {
                                    "name": command.name,
                                    "description": command.description,
                                    "aliases": [],
                                    "signature": "",
                                    "help": command.description,
                                },
                            )()
                            available_commands[command.name] = mock_command
        except Exception as e:
            # Fehler beim Sammeln von App-Commands ignorieren
            logger.debug(f"Fehler beim Sammeln von App-Commands: {e}")

        return available_commands

    async def _can_use_app_command(self, command, ctx):
        """Prüft ob ein Benutzer einen App-Command verwenden kann"""
        try:
            # Prüfe Default-Permissions
            if (
                hasattr(command, "_default_permissions")
                and command._default_permissions
            ):
                # App-Command hat spezielle Default-Permissions
                required_perms = command._default_permissions
                if not ctx.author.guild_permissions >= required_perms:
                    return False

            # Verwende das zentrale Permission-System
            return await self._check_command_permission(command.name, ctx)

        except Exception as e:
            # Bei Fehlern: Command nicht anzeigen für Sicherheit
            logger.debug(
                f"Fehler bei App-Command-Berechtigung-Prüfung für {command.name}: {e}"
            )
            return False

    def _get_command_permissions_map(self):
        """Gibt eine Zuordnung von Command-Namen zu erforderlichen Berechtigungen zurück"""
        return {
            # Owner-only commands
            "sync": "is_owner",
            "shutdown": "is_owner",
            "reload": "is_owner",
            "load": "is_owner",
            "unload": "is_owner",
            "listcogs": "is_owner",
            "reloadall": "is_owner",
            # Administrator commands
            "birthday_test": "administrator",
            "birthday_status": "administrator",
            "config": "administrator",
            "specs_clean": "administrator",  # specs clean subcommand
            # Manage messages
            "purge": "manage_messages",
            # Manage channels
            "computerbase_info": "manage_channels",
            "computerbase_test": "manage_channels",
            "pcgh_info": "manage_channels",
            "pcgh_test": "manage_channels",
            "hardwareluxx_info": "manage_channels",
            "hardwareluxx_test": "manage_channels",
            "software_info": "manage_channels",
            "software_test": "manage_channels",
            # Commands available to everyone (explicitly listed for clarity)
            "ping": None,
            "botinfo": None,
            "serverinfo": None,
            "userinfo": None,
            "roll": None,
            "8ball": None,
            "gif": None,
            "random": None,
            "why": None,
            "wetter": None,
            "weathershort": None,
            "hwbot": None,
            "screenshot": None,
            "specs": None,  # Main specs command
            "cpu": None,
            "curve": None,
            "limit": None,
            "liste": None,
            "anleitung": None,
            "ramkit": None,
            "spd": None,
            "mainboard": None,
            "bios": None,
            "leetspeak": None,
            "schmutz": None,
            "sgehdn": None,
            "geburtstag": None,
            "stats": None,
            "mystats": None,
        }

    async def _check_command_permission(self, command_name, ctx):
        """Prüft ob ein Benutzer einen Command basierend auf Namen verwenden kann"""
        permission_map = self._get_command_permissions_map()
        required_permission = permission_map.get(command_name)

        if required_permission == "is_owner":
            return await self.bot.is_owner(ctx.author)
        elif required_permission == "administrator":
            return ctx.author.guild_permissions.administrator
        elif required_permission == "manage_messages":
            return ctx.author.guild_permissions.manage_messages
        elif required_permission == "manage_channels":
            return ctx.author.guild_permissions.manage_channels
        elif required_permission is None:
            return True  # Für alle verfügbar
        else:
            # Unbekannte Berechtigung - für Sicherheit nicht anzeigen
            return False

    async def _show_command_help(self, ctx, command_name: str):
        """Zeigt Hilfe für einen spezifischen Befehl an"""

        # Entferne Präfix falls vorhanden
        command_name = command_name.lstrip("/!")

        # Suche den Befehl
        command = self.bot.get_command(command_name)

        if not command:
            embed = EmbedFactory.error_embed(
                "Befehl nicht gefunden",
                f"Der Befehl `{command_name}` existiert nicht.\nVerwende `/help` um alle verfügbaren Befehle zu sehen.",
            )
            await ctx.send(embed=embed)
            return

        # Prüfe ob der Benutzer den Befehl verwenden kann
        try:
            can_run = await command.can_run(ctx)
            if not can_run:
                embed = EmbedFactory.error_embed(
                    "Keine Berechtigung",
                    f"Du hast keine Berechtigung, den Befehl `{command_name}` zu verwenden.",
                )
                await ctx.send(embed=embed)
                return
        except commands.CommandError:
            embed = EmbedFactory.error_embed(
                "Keine Berechtigung",
                f"Du hast keine Berechtigung, den Befehl `{command_name}` zu verwenden.",
            )
            await ctx.send(embed=embed)
            return

        # Erstelle detaillierte Befehl-Hilfe
        embed = EmbedFactory.info_command_embed(
            title=f"Hilfe für `/{command.name}`",
            description=command.description or "Keine Beschreibung verfügbar.",
            requester=ctx.author,
        )

        # Aliases
        if command.aliases:
            embed.add_field(
                name="Aliase",
                value=", ".join([f"`/{alias}`" for alias in command.aliases]),
                inline=False,
            )

        # Parameter
        if command.signature:
            embed.add_field(
                name="Parameter",
                value=f"`/{command.name} {command.signature}`",
                inline=False,
            )

        # Hilfetext
        if command.help:
            embed.add_field(name="Beschreibung", value=command.help, inline=False)

        # Berechtigungen
        if hasattr(command, "checks") and command.checks:
            permissions = []
            for check in command.checks:
                if hasattr(check, "__name__"):
                    if "admin" in check.__name__.lower():
                        permissions.append("Administrator")
                    elif "manage" in check.__name__.lower():
                        permissions.append("Server verwalten")

            if permissions:
                embed.add_field(
                    name="Erforderliche Berechtigungen",
                    value=", ".join(permissions),
                    inline=False,
                )

        # Beispiele für häufige Befehle
        examples = {
            "specs": [
                "**Anzeigen:**",
                "`/specs` - Zeigt deine eigenen Spezifikationen",
                "`/specs @Benutzer` - Zeigt Specs eines anderen Benutzers",
                "`/specs show @Benutzer` - Alternative zum obigen Befehl",
                "",
                "**Verwalten:**",
                "`/specs set RTX 4080, i7-13700K, 32GB DDR5` - Setze deine Hardware-Specs",
                "`/specs delete` - Lösche deine Spezifikationen",
                "`/specs raw` - Zeige deine Specs als bearbeitbaren Text",
                "",
                "**Suchen:**",
                "`/specs search RTX 4080` - Suche nach Hardware in allen Specs",
                "`/specs search AMD` - Finde alle mit AMD-Hardware",
                "",
                "**Admin:**",
                "`/specs clean` - Bereinige verwaiste Einträge (nur Admin)",
            ],
            "weather": [
                "`/weather Berlin` - Wetter für Berlin",
                "`/weather München, DE` - Wetter für München",
            ],
            "roll": ["`/roll` - Würfelt 1-100", "`/roll 20` - Würfelt 1-20"],
            "geburtstag": [
                "`/geburtstag hinzufügen` - Füge dein Geburtsdatum hinzu",
                "`/geburtstag anzeigen @Benutzer` - Zeige Geburtstag eines Benutzers",
                "`/geburtstag liste` - Liste alle Geburtstage im Server",
            ],
            "birthday_test": [
                "`/birthday_test` - Testet die Geburtstags-Benachrichtigungen (Admin)",
            ],
            "birthday_status": [
                "`/birthday_status` - Zeigt Status der Geburtstags-Funktionen (Admin)",
            ],
            "config": [
                "`/config` - Zeigt oder ändert die Serverkonfiguration (Admin)",
            ],
            "purge": [
                "`/purge 10` - Löscht die letzten 10 Nachrichten",
                "`/purge 50` - Löscht die letzten 50 Nachrichten",
            ],
        }

        if command.name in examples:
            embed.add_field(
                name="Beispiele", value="\n".join(examples[command.name]), inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    """Lädt das Help Cog"""
    await bot.add_cog(Help(bot))
    logger.info("Help Cog geladen")
