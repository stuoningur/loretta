"""
Purge Befehle für den Loretta Discord Bot
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import EmbedFactory
from utils.responses import send_error_response, send_response
from utils.logging import log_command_success, log_command_error
from utils.decorators import track_command_usage

logger = logging.getLogger(__name__)


class Purge(commands.Cog):
    """Purge Befehle und Funktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="purge",
        description="Löscht eine bestimmte Anzahl von Nachrichten aus dem aktuellen Kanal",
    )
    @commands.has_permissions(manage_messages=True)
    @track_command_usage
    async def purge(self, ctx, anzahl: int):
        """Löscht eine bestimmte Anzahl von Nachrichten"""

        # Validierung der Eingabe
        if anzahl <= 0:
            await send_error_response(
                ctx,
                "Ungültige Eingabe",
                "Die Anzahl muss größer als 0 sein!",
                ephemeral=True,
            )
            return

        if anzahl > 100:
            await send_error_response(
                ctx,
                "Limit überschritten",
                "Es können maximal 100 Nachrichten auf einmal gelöscht werden!",
                ephemeral=True,
            )
            return

        try:
            # Für Slash-Commands: Defer die Interaction da der Purge-Vorgang Zeit brauchen kann
            if ctx.interaction:
                await ctx.defer(ephemeral=True)

            # Lösche Nachrichten (bulk_delete funktioniert nur für Nachrichten jünger als 14 Tage)
            if ctx.interaction:
                # Slash Command - lösche nur die angegebene Anzahl
                deleted = await ctx.channel.purge(limit=anzahl)
                deleted_count = len(deleted)
            else:
                # Prefix Command - lösche Nachrichten und den Befehl selbst
                deleted = await ctx.channel.purge(limit=anzahl + 1)
                deleted_count = len(deleted) - 1

            # Sende Erfolgs-Response
            success_embed = EmbedFactory.success_embed(
                "Nachrichten gelöscht",
                f"{deleted_count} Nachrichten wurden erfolgreich gelöscht.",
            )
            await send_response(
                ctx, success_embed, ephemeral=ctx.interaction is not None
            )

            log_command_success(
                logger,
                "purge",
                ctx.author,
                ctx.guild,
                deleted_messages=deleted_count,
                channel=getattr(ctx.channel, "name", "Unbekannter Kanal"),
            )

        except discord.Forbidden as e:
            await send_error_response(
                ctx,
                "Fehlende Berechtigung",
                "Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu löschen!",
                ephemeral=True,
            )
            log_command_error(
                logger,
                "purge",
                ctx.author,
                ctx.guild,
                e,
                channel=getattr(ctx.channel, "name", "Unbekannter Kanal"),
            )

        except discord.HTTPException as e:
            await send_error_response(
                ctx,
                "Fehler beim Löschen",
                "Fehler beim Löschen der Nachrichten. Möglicherweise sind die Nachrichten zu alt (älter als 14 Tage).",
                ephemeral=True,
            )
            log_command_error(logger, "purge", ctx.author, ctx.guild, e)


@app_commands.context_menu(name="Löschen bis hier")
@app_commands.default_permissions(manage_messages=True)
async def delete_up_to_message(
    interaction: discord.Interaction, message: discord.Message
):
    """Löscht alle Nachrichten bis zur ausgewählten Nachricht (einschließlich)"""

    try:
        # Defer die Interaction sofort da der Vorgang Zeit brauchen kann
        await interaction.response.defer(ephemeral=True)

        # Überprüfe ob es sich um einen Text-Kanal handelt
        if not isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            embed = discord.Embed(
                title="Ungültiger Kanal",
                description="Dieser Befehl kann nur in Text-Kanälen verwendet werden!",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        # Überprüfe Berechtigungen
        if not isinstance(interaction.user, discord.Member):
            embed = discord.Embed(
                title="Nur auf Servern",
                description="Dieser Befehl kann nur auf Servern verwendet werden!",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            embed = discord.Embed(
                title="Fehlende Berechtigung",
                description="Du hast keine Berechtigung, Nachrichten zu verwalten!",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        # Hole alle Nachrichten nach der ausgewählten Nachricht
        messages_to_delete = []

        async for msg in interaction.channel.history(after=message, limit=None):
            messages_to_delete.append(msg)

        # Füge die ausgewählte Nachricht hinzu
        messages_to_delete.append(message)

        if not messages_to_delete:
            embed = discord.Embed(
                title="Keine Nachrichten",
                description="Keine Nachrichten zum Löschen gefunden!",
                color=discord.Color.blurple(),
            )
            await interaction.followup.send(embed=embed)
            return

        if len(messages_to_delete) > 100:
            embed = discord.Embed(
                title="Limit überschritten",
                description=f"Es wurden {len(messages_to_delete)} Nachrichten gefunden, aber maximal 100 können auf einmal gelöscht werden!",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        # Lösche die Nachrichten
        await interaction.channel.delete_messages(messages_to_delete)

        # Sende Bestätigung
        embed = discord.Embed(
            title="Nachrichten gelöscht",
            description=f"{len(messages_to_delete)} Nachrichten wurden erfolgreich gelöscht.",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)

        logger.info(
            f"Kontext-Menu Löschung ausgeführt von {interaction.user} in {getattr(interaction.channel, 'name', 'Unbekannter Kanal')}: {len(messages_to_delete)} Nachrichten gelöscht"
        )

    except discord.Forbidden:
        embed = discord.Embed(
            title="Fehlende Berechtigung",
            description="Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu löschen!",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed)
        logger.warning(
            f"Keine Berechtigung für Kontext-Menu Löschung in {getattr(interaction.channel, 'name', 'Unbekannter Kanal')} durch {interaction.user}"
        )

    except discord.HTTPException as e:
        embed = discord.Embed(
            title="Fehler beim Löschen",
            description="Fehler beim Löschen der Nachrichten. Möglicherweise sind einige Nachrichten zu alt (älter als 14 Tage).",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed)
        logger.error(f"Fehler beim Kontext-Menu Löschung: {e}")


async def setup(bot):
    """Lädt das Purge Cog"""
    cog = Purge(bot)
    await bot.add_cog(cog)

    # Füge das Kontext-Menü zum Command Tree hinzu
    bot.tree.add_command(delete_up_to_message)

    logger.info("Purge Cog geladen")
