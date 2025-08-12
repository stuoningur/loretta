"""
Cog-Management-Befehle für den Loretta Discord Bot
Enthält Cog-Management-Befehle (laden, entladen, neuladen)
"""

import logging
from pathlib import Path

import discord
from discord.ext import commands

from src.bot.utils.decorators import track_command_usage

# Constants
MAX_ERROR_MESSAGE_LENGTH = 50
MAX_DISCORD_FIELD_LENGTH = 1024

logger = logging.getLogger(__name__)


class CogManagement(commands.Cog):
    """Cog-Management-Befehle für Bot-Management"""

    def __init__(self, bot):
        self.bot = bot

    def _find_cog_path(self, cog_name: str) -> str | None:
        """Findet den vollständigen Pfad eines Cogs basierend auf dem Namen"""
        # Entferne "cogs." Präfix falls vorhanden
        if cog_name.startswith("cogs."):
            cog_name = cog_name.replace("cogs.", "")

        # Basispfad für Cogs
        cogs_base = Path("src/bot/cogs")

        # Suche in allen Unterordnern
        for cog_file in cogs_base.rglob(f"{cog_name}.py"):
            if cog_file.name.startswith("__"):
                continue

            # Konvertiere Pfad zu Modul-Import-Pfad
            relative_path = cog_file.relative_to(Path("."))
            module_path = str(relative_path.with_suffix("")).replace("/", ".")
            return module_path

        return None

    def _get_available_cogs(self) -> list[str]:
        """Sammelt alle verfügbaren Cogs aus allen Unterordnern"""
        cogs_base = Path("src/bot/cogs")
        available_cogs = []

        for cog_file in cogs_base.rglob("*.py"):
            if cog_file.name.startswith("__"):
                continue

            # Konvertiere Pfad zu Modul-Import-Pfad
            relative_path = cog_file.relative_to(Path("."))
            module_path = str(relative_path.with_suffix("")).replace("/", ".")
            available_cogs.append(module_path)

        return available_cogs

    @commands.hybrid_command(
        name="reload",
        description="Lädt ein Cog neu",
    )
    @commands.is_owner()
    @track_command_usage
    async def reload_cog(self, ctx, *, cog_name: str):
        """Lädt ein spezifisches Cog neu"""

        # Finde den vollständigen Pfad des Cogs
        full_path = self._find_cog_path(cog_name)
        if not full_path:
            embed = discord.Embed(
                title="Fehler beim Neuladen",
                description=f"Cog `{cog_name}` wurde nicht gefunden.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog '{cog_name}' wurde nicht gefunden")
            return

        try:
            # Versuche das Cog neu zu laden
            await self.bot.reload_extension(full_path)

            embed = discord.Embed(
                title="Cog neu geladen",
                description=f"`{cog_name}` wurde erfolgreich neu geladen.",
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed)
            logger.info(f"Cog '{cog_name}' wurde von {ctx.author} neu geladen")

        except commands.ExtensionNotLoaded:
            embed = discord.Embed(
                title="Fehler beim Neuladen",
                description=f"Cog `{cog_name}` ist nicht geladen.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog '{cog_name}' ist nicht geladen")

        except Exception as e:
            embed = discord.Embed(
                title="Fehler beim Neuladen",
                description=f"Fehler beim Neuladen von `{cog_name}`: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Fehler beim Neuladen von Cog '{cog_name}': {e}")

    @commands.hybrid_command(
        name="load",
        description="Lädt ein Cog",
    )
    @commands.is_owner()
    @track_command_usage
    async def load_cog(self, ctx, *, cog_name: str):
        """Lädt ein spezifisches Cog"""

        # Finde den vollständigen Pfad des Cogs
        full_path = self._find_cog_path(cog_name)
        if not full_path:
            embed = discord.Embed(
                title="Fehler beim Laden",
                description=f"Cog `{cog_name}` wurde nicht gefunden.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog '{cog_name}' wurde nicht gefunden")
            return

        try:
            # Versuche das Cog zu laden
            await self.bot.load_extension(full_path)

            embed = discord.Embed(
                title="Cog geladen",
                description=f"`{cog_name}` wurde erfolgreich geladen.",
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed)
            logger.info(f"Cog '{cog_name}' wurde von {ctx.author} geladen")

        except commands.ExtensionAlreadyLoaded:
            embed = discord.Embed(
                title="Fehler beim Laden",
                description=f"Cog `{cog_name}` ist bereits geladen.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog `{cog_name}` ist bereits geladen.")

        except Exception as e:
            embed = discord.Embed(
                title="Fehler beim Laden",
                description=f"Fehler beim Laden von `{cog_name}`: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Fehler beim Laden von Cog '{cog_name}': {e}")

    @commands.hybrid_command(
        name="unload",
        description="Entlädt ein Cog",
    )
    @commands.is_owner()
    @track_command_usage
    async def unload_cog(self, ctx, *, cog_name: str):
        """Entlädt ein spezifisches Cog"""

        # Verhindere das Entladen des CogManagement-Cogs
        if cog_name.lower() == "cog_management":
            embed = discord.Embed(
                title="Fehler beim Entladen",
                description="Das CogManagement-Cog kann nicht entladen werden.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        # Finde den vollständigen Pfad des Cogs
        full_path = self._find_cog_path(cog_name)
        if not full_path:
            embed = discord.Embed(
                title="Fehler beim Entladen",
                description=f"Cog `{cog_name}` wurde nicht gefunden.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog '{cog_name}' wurde nicht gefunden")
            return

        try:
            # Versuche das Cog zu entladen
            await self.bot.unload_extension(full_path)

            embed = discord.Embed(
                title="Cog entladen",
                description=f"`{cog_name}` wurde erfolgreich entladen.",
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed)
            logger.info(f"Cog '{cog_name}' wurde von {ctx.author} entladen")

        except commands.ExtensionNotLoaded:
            embed = discord.Embed(
                title="Fehler beim Entladen",
                description=f"Cog `{cog_name}` ist nicht geladen.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Cog `{cog_name}` ist nicht geladen.")

        except Exception as e:
            embed = discord.Embed(
                title="Fehler beim Entladen",
                description=f"Fehler beim Entladen von `{cog_name}`: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(f"Fehler beim Entladen von Cog '{cog_name}': {e}")

    @commands.hybrid_command(
        name="listcogs",
        description="Zeigt alle verfügbaren und geladenen Cogs an",
    )
    @commands.is_owner()
    @track_command_usage
    async def list_cogs(self, ctx):
        """Zeigt eine Liste aller verfügbaren und geladenen Cogs"""

        # Sammle alle verfügbaren Cogs
        available_cogs = self._get_available_cogs()

        # Geladene Cogs
        loaded_cogs = list(self.bot.extensions.keys())

        embed = discord.Embed(title="Cog-Übersicht", color=discord.Color.blurple())

        # Verfügbare Cogs nach Kategorien gruppieren
        if available_cogs:
            categories = {}
            for cog_path in sorted(available_cogs):
                # Extrahiere Kategorie und Cog-Namen
                parts = cog_path.split(".")
                if len(parts) >= 4:  # src.bot.cogs.category.cog_name
                    category = parts[3]  # category
                    cog_name = parts[4]  # cog_name

                    if category not in categories:
                        categories[category] = []

                    status = (
                        "[GELADEN]" if cog_path in loaded_cogs else "[NICHT GELADEN]"
                    )
                    categories[category].append(f"{status} `{cog_name}`")

            # Zeige Cogs nach Kategorien an
            for category, cogs in categories.items():
                category_text = "\n".join(cogs)
                if len(category_text) > MAX_DISCORD_FIELD_LENGTH:
                    category_text = (
                        category_text[: MAX_DISCORD_FIELD_LENGTH - 3] + "..."
                    )

                embed.add_field(
                    name=f"{category.title()}", value=category_text, inline=True
                )

        # Statistiken
        embed.add_field(
            name="Statistiken",
            value=f"**Geladen:** {len(loaded_cogs)}\n**Verfügbar:** {len(available_cogs)}",
            inline=False,
        )

        await ctx.send(embed=embed)
        logger.info(f"Cog-Liste wurde von {ctx.author} angezeigt")

    @commands.hybrid_command(
        name="reloadall",
        description="Lädt alle geladenen Cogs neu",
    )
    @commands.is_owner()
    @track_command_usage
    async def reload_all_cogs(self, ctx):
        """Lädt alle momentan geladenen Cogs neu"""

        loaded_cogs = list(self.bot.extensions.keys())

        if not loaded_cogs:
            embed = discord.Embed(
                title="Keine Cogs zum Neuladen",
                description="Es sind keine Cogs geladen.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        success_count = 0
        failed_cogs = []

        # Temporäre Nachricht senden
        temp_embed = discord.Embed(
            title="Lade alle Cogs neu...",
            description=f"Bearbeite {len(loaded_cogs)} Cogs...",
            color=discord.Color.blurple(),
        )
        message = await ctx.send(embed=temp_embed)

        for cog_name in loaded_cogs:
            try:
                await self.bot.reload_extension(cog_name)
                success_count += 1
            except Exception as e:
                failed_cogs.append((cog_name, str(e)))
                logger.error(f"Fehler beim Neuladen von Cog '{cog_name}': {e}")

        # Ergebnis anzeigen
        if failed_cogs:
            embed = discord.Embed(
                title="Cogs teilweise neu geladen", color=discord.Color.blurple()
            )

            embed.add_field(
                name="Erfolgreich",
                value=f"{success_count} Cogs neu geladen",
                inline=False,
            )

            failed_text = ""
            for cog_name, error in failed_cogs:
                cog_display = cog_name.replace("cogs.", "")
                failed_text += (
                    f"FEHLER `{cog_display}`: {error[:MAX_ERROR_MESSAGE_LENGTH]}...\n"
                )

            embed.add_field(
                name="Fehlgeschlagen",
                value=failed_text[:MAX_DISCORD_FIELD_LENGTH],  # Discord-Limit
                inline=False,
            )
        else:
            embed = discord.Embed(
                title="Alle Cogs neu geladen",
                description=f"{success_count} Cogs wurden erfolgreich neu geladen.",
                color=discord.Color.green(),
            )

        await message.edit(embed=embed)
        logger.info(
            f"Alle Cogs wurden von {ctx.author} neu geladen ({success_count} erfolgreich, {len(failed_cogs)} fehlgeschlagen)"
        )


async def setup(bot):
    """Lädt das CogManagement Cog"""
    await bot.add_cog(CogManagement(bot))
    logger.info("CogManagement Cog geladen")
