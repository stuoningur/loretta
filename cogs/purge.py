"""
Purge Befehle für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

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
    async def purge(self, ctx, anzahl: int):
        """Löscht eine bestimmte Anzahl von Nachrichten"""

        # Validierung der Eingabe
        if anzahl <= 0:
            await ctx.send("Die Anzahl muss größer als 0 sein!", ephemeral=True)
            return

        if anzahl > 100:
            await ctx.send(
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
                # Follow-up response für Slash-Commands
                await ctx.interaction.followup.send(
                    f"{len(deleted)} Nachrichten wurden erfolgreich gelöscht."
                )
            else:
                # Prefix Command - lösche Nachrichten und den Befehl selbst
                deleted = await ctx.channel.purge(limit=anzahl + 1)
                # Bestätigungsnachricht
                confirmation = await ctx.send(
                    f"{len(deleted) - 1} Nachrichten wurden erfolgreich gelöscht."
                )
                # Lösche die Bestätigungsnachricht nach 5 Sekunden
                await confirmation.delete(delay=5)

            logger.info(
                f"Purge-Befehl ausgeführt von {ctx.author} in {getattr(ctx.channel, 'name', 'Unbekannter Kanal')}: {len(deleted) if ctx.interaction else len(deleted) - 1} Nachrichten gelöscht"
            )

        except discord.Forbidden:
            error_msg = (
                "Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu löschen!"
            )
            if ctx.interaction and ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(error_msg)
            else:
                await ctx.send(error_msg, ephemeral=True)
            logger.warning(
                f"Keine Berechtigung für Purge in {getattr(ctx.channel, 'name', 'Unbekannter Kanal')} durch {ctx.author}"
            )

        except discord.HTTPException as e:
            error_msg = "Fehler beim Löschen der Nachrichten. Möglicherweise sind die Nachrichten zu alt (älter als 14 Tage)."
            if ctx.interaction and ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(error_msg)
            else:
                await ctx.send(error_msg, ephemeral=True)
            logger.error(f"Fehler beim Purge-Befehl: {e}")

    @purge.error
    async def purge_error(self, ctx, error):
        """Error handler für den purge command"""
        error_msg = None

        if isinstance(error, commands.MissingPermissions):
            error_msg = "Du hast keine Berechtigung, Nachrichten zu verwalten!"
        elif isinstance(error, commands.BadArgument):
            error_msg = "Bitte gib eine gültige Zahl ein!"
        elif isinstance(error, commands.MissingRequiredArgument):
            error_msg = "Bitte gib die Anzahl der zu löschenden Nachrichten an!\nBeispiel: `/purge 10`"
        else:
            logger.error(f"Unbehandelter Fehler im purge command: {error}")
            error_msg = "Ein unerwarteter Fehler ist aufgetreten."

        # Sende die Fehlermeldung entsprechend dem Command-Typ
        if ctx.interaction and ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(error_msg)
        else:
            await ctx.send(error_msg, ephemeral=True)


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
            await interaction.followup.send(
                "Dieser Befehl kann nur in Text-Kanälen verwendet werden!"
            )
            return

        # Überprüfe Berechtigungen
        if not isinstance(interaction.user, discord.Member):
            await interaction.followup.send(
                "Dieser Befehl kann nur auf Servern verwendet werden!"
            )
            return

        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.followup.send(
                "Du hast keine Berechtigung, Nachrichten zu verwalten!"
            )
            return

        # Hole alle Nachrichten nach der ausgewählten Nachricht
        messages_to_delete = []

        async for msg in interaction.channel.history(after=message, limit=None):
            messages_to_delete.append(msg)

        # Füge die ausgewählte Nachricht hinzu
        messages_to_delete.append(message)

        if not messages_to_delete:
            await interaction.followup.send("Keine Nachrichten zum Löschen gefunden!")
            return

        if len(messages_to_delete) > 100:
            await interaction.followup.send(
                f"Es wurden {len(messages_to_delete)} Nachrichten gefunden, aber maximal 100 können auf einmal gelöscht werden!"
            )
            return

        # Lösche die Nachrichten
        await interaction.channel.delete_messages(messages_to_delete)

        # Sende Bestätigung
        await interaction.followup.send(
            f"{len(messages_to_delete)} Nachrichten wurden erfolgreich gelöscht."
        )

        logger.info(
            f"Kontext-Menu Löschung ausgeführt von {interaction.user} in {getattr(interaction.channel, 'name', 'Unbekannter Kanal')}: {len(messages_to_delete)} Nachrichten gelöscht"
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu löschen!"
        )
        logger.warning(
            f"Keine Berechtigung für Kontext-Menu Löschung in {getattr(interaction.channel, 'name', 'Unbekannter Kanal')} durch {interaction.user}"
        )

    except discord.HTTPException as e:
        await interaction.followup.send(
            "Fehler beim Löschen der Nachrichten. Möglicherweise sind einige Nachrichten zu alt (älter als 14 Tage)."
        )
        logger.error(f"Fehler beim Kontext-Menu Löschung: {e}")


async def setup(bot):
    """Lädt das Purge Cog"""
    cog = Purge(bot)
    await bot.add_cog(cog)

    # Füge das Kontext-Menü zum Command Tree hinzu
    bot.tree.add_command(delete_up_to_message)

    logger.info("Purge Cog geladen")
