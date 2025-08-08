"""
Geburtstagskommandos, -verwaltung und tägliche Benachrichtigungen
"""

import calendar
import logging
from datetime import date, time
from typing import List, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.database import Birthday
from utils.constants import GERMAN_MONTH_NAMES
from utils.responses import send_error_response
from utils.embeds import EmbedFactory
from utils.user_resolver import UserResolver
from utils.decorators import track_command_usage

# Constants
BIRTHDAY_INPUT_MAX_LENGTH = 6
BIRTHDAY_INPUT_MIN_LENGTH = 5
BIRTHDAY_NOTIFICATION_HOUR = 9
BIRTHDAY_NOTIFICATION_MINUTE = 0
BIRTHDAY_NOTIFICATION_SECOND = 0
MIN_MONTH = 1
MAX_MONTH = 12
MIN_DAY = 1
MAX_DAY = 31
DOT_COUNT_IN_DATE = 2
DATE_PARTS = 2
SINGLE_BIRTHDAY_COUNT = 1
MAX_EMBED_DESCRIPTION_LENGTH = 4000

logger = logging.getLogger(__name__)


class BirthdayModal(discord.ui.Modal):
    """Modal für Geburtsdatums-Eingabe"""

    def __init__(self, user: Union[discord.Member, discord.User]):
        super().__init__(title=f"Geburtstag für {user.display_name}")
        self.user = user

        self.birthday_input = discord.ui.TextInput(
            label="Geburtsdatum",
            placeholder="Format: DD.MM. (z.B. 25.12.)",
            max_length=BIRTHDAY_INPUT_MAX_LENGTH,
            min_length=BIRTHDAY_INPUT_MIN_LENGTH,
        )
        self.add_item(self.birthday_input)

    async def on_submit(self, interaction: discord.Interaction):
        from discord.ext.commands import Bot

        if not isinstance(interaction.client, Bot):
            return
        cog = interaction.client.get_cog("BirthdayCog")
        if not cog or not isinstance(cog, BirthdayCog):
            return

        birthday_str = self.birthday_input.value.strip()
        await cog.save_birthday_from_string(interaction, self.user, birthday_str)


class BirthdayCog(commands.Cog):
    """Cog für Geburtstagsverwaltung und automatische Benachrichtigungen"""

    def __init__(self, bot):
        self.bot = bot
        self.birthday_messages = [
            "🎉 Herzlichen Glückwunsch zum Geburtstag, {user}! 🎂",
            "🎂 Alles Gute zum Geburtstag, {user}! 🎉",
            "🎈 Happy Birthday, {user}! Hab einen wunderschönen Tag! 🎁",
            "🎉 Ein wundervoller Geburtstag für {user}! 🎂 Feier schön!",
            "🎂 {user} hat heute Geburtstag! Herzlichen Glückwunsch! 🎈",
        ]

    async def cog_load(self):
        """Wird beim Laden des Cogs ausgeführt"""
        if not self.daily_birthday_check.is_running():
            self.daily_birthday_check.start()
            logger.info("Tägliche Geburtstagsüberprüfung gestartet")

    async def cog_unload(self):
        """Wird beim Entladen des Cogs ausgeführt"""
        self.daily_birthday_check.cancel()
        logger.info("Tägliche Geburtstagsüberprüfung gestoppt")

    @tasks.loop(
        time=time(
            hour=BIRTHDAY_NOTIFICATION_HOUR,
            minute=BIRTHDAY_NOTIFICATION_MINUTE,
            second=BIRTHDAY_NOTIFICATION_SECOND,
        )
    )  # 9:00 Uhr täglich
    async def daily_birthday_check(self):
        """Überprüft täglich auf Geburtstage und sendet Benachrichtigungen"""
        try:
            logger.info("Beginne tägliche Geburtstagsüberprüfung...")

            # Hole alle Geburtstage für heute
            today_birthdays = await self.bot.db.get_birthdays_today()

            if not today_birthdays:
                logger.info("Keine Geburtstage heute gefunden")
                return

            logger.info(f"Gefunden: {len(today_birthdays)} Geburtstage heute")

            # Gruppiere Geburtstage nach Guild
            guild_birthdays = {}
            for birthday in today_birthdays:
                if birthday.guild_id not in guild_birthdays:
                    guild_birthdays[birthday.guild_id] = []
                guild_birthdays[birthday.guild_id].append(birthday)

            # Sende Benachrichtigungen für jede Guild
            for guild_id, birthdays in guild_birthdays.items():
                await self._send_birthday_notifications(guild_id, birthdays)

            logger.info("Tägliche Geburtstagsüberprüfung abgeschlossen")

        except Exception as e:
            logger.error(
                f"Fehler bei der täglichen Geburtstagsüberprüfung: {e}", exc_info=True
            )

    @daily_birthday_check.before_loop
    async def before_birthday_check(self):
        """Wartet bis der Bot bereit ist"""
        await self.bot.wait_until_ready()
        logger.info("Bot ist bereit - Geburtstagsüberprüfung kann starten")

    async def _send_birthday_notifications(
        self, guild_id: int, birthdays: List[Birthday]
    ):
        """Sendet Geburtstags-Benachrichtigungen für eine Guild"""
        try:
            # Hole die Guild
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"Guild {guild_id} nicht gefunden")
                return

            # Hole den konfigurierten Geburtstags-Kanal für diese Guild
            birthday_channel_id = await self.bot.db.get_birthday_channel(guild_id)

            if not birthday_channel_id:
                logger.info(
                    f"Kein Geburtstags-Kanal für Guild {guild.name} konfiguriert"
                )
                return

            # Hole das Channel-Objekt
            birthday_channel = guild.get_channel(birthday_channel_id)
            if not birthday_channel:
                logger.warning(
                    f"Geburtstags-Kanal {birthday_channel_id} für Guild {guild.name} nicht gefunden"
                )
                return

            # Bereite die Nachrichten vor
            birthday_users = []
            for birthday in birthdays:
                member = guild.get_member(birthday.user_id)
                if member:  # Nur wenn der Benutzer noch im Server ist
                    birthday_users.append((member, birthday))
                else:
                    logger.debug(
                        f"Benutzer {birthday.user_id} nicht mehr in Guild {guild_id}"
                    )

            if not birthday_users:
                logger.info(
                    f"Keine aktiven Benutzer mit Geburtstagen in Guild {guild.name}"
                )
                return

            # Überprüfe Bot-Berechtigungen
            if not birthday_channel.permissions_for(guild.me).send_messages:
                logger.warning(
                    f"Keine Berechtigung zum Senden in Kanal {birthday_channel.name} in Guild {guild.name}"
                )
                return

            # Sende Nachricht in den konfigurierten Kanal
            await self._send_birthday_message(birthday_channel, birthday_users)

        except Exception as e:
            logger.error(
                f"Fehler beim Senden von Geburtstags-Benachrichtigungen für Guild {guild_id}: {e}",
                exc_info=True,
            )

    async def _send_birthday_message(
        self, channel: discord.TextChannel, birthday_users: List[tuple]
    ):
        """Sendet eine Geburtstags-Nachricht in einen Kanal"""
        try:
            if len(birthday_users) == SINGLE_BIRTHDAY_COUNT:
                # Einzelner Geburtstag
                member, _ = birthday_users[0]

                # Wähle eine zufällige Nachricht
                import random

                message_template = random.choice(self.birthday_messages)
                message = message_template.format(user=member.mention)

                # Erstelle Embed
                embed = EmbedFactory.single_birthday_embed(member, message)
                await channel.send(embed=embed)

            else:
                # Mehrere Geburtstage
                user_mentions = [member.mention for member, _ in birthday_users]

                # Erstelle Embed für mehrere Geburtstage
                embed = EmbedFactory.multiple_birthdays_embed(user_mentions)
                await channel.send(embed=embed)

            logger.info(
                f"Geburtstags-Nachricht gesendet in {channel.name} ({channel.guild.name})"
            )

        except Exception as e:
            logger.error(
                f"Fehler beim Senden der Geburtstags-Nachricht in {channel.name}: {e}",
                exc_info=True,
            )

    # Slash Commands
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.command(
        name="geburtstag",
        description="Verwalte Geburtstage - hinzufügen, entfernen oder anzeigen",
    )
    @app_commands.describe(
        aktion="Was möchtest du tun?",
        user="Benutzer für den die Aktion ausgeführt werden soll (nur für Admins)",
    )
    @app_commands.choices(
        aktion=[
            app_commands.Choice(name="hinzufügen", value="add"),
            app_commands.Choice(name="entfernen", value="remove"),
            app_commands.Choice(name="anzeigen", value="show"),
            app_commands.Choice(name="liste", value="list"),
        ]
    )
    async def birthday(
        self,
        interaction: discord.Interaction,
        aktion: app_commands.Choice[str],
        user: Optional[str] = None,
    ):
        """Hauptkommando für Geburtstage"""
        if not interaction.guild:
            await send_error_response(
                interaction,
                "Fehler",
                "Dieser Befehl kann nur in einem Server verwendet werden.",
                ephemeral=True,
            )
            return

        # Bestimme den Zielbenutzer
        target_user = interaction.user

        if user:
            # Verwende UserResolver für bessere Benutzersuche
            # Erstelle einen temporären Context für UserResolver
            from discord.ext import commands

            ctx = await commands.Context.from_interaction(interaction)
            target_user = await UserResolver.resolve_user(ctx, user)
            if not target_user:
                return

        if aktion.value == "add":
            await self._handle_add_birthday(interaction, target_user)
        elif aktion.value == "remove":
            await self._handle_remove_birthday(interaction, target_user)
        elif aktion.value == "show":
            await self._handle_show_birthday(interaction, target_user)
        elif aktion.value == "list":
            await self._handle_list_birthdays(interaction)

    async def _handle_add_birthday(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
    ):
        """Behandelt das Hinzufügen eines Geburtstags"""
        modal = BirthdayModal(user)
        await interaction.response.send_modal(modal)

    async def _handle_remove_birthday(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
    ):
        """Behandelt das Entfernen eines Geburtstags"""
        if not interaction.guild:
            return

        try:
            birthday = await self.bot.db.get_birthday(interaction.guild.id, user.id)

            if not birthday:
                await send_error_response(
                    interaction,
                    "Kein Geburtstag gefunden",
                    f"Es ist kein Geburtstag für {user.display_name} gespeichert.",
                    ephemeral=True,
                )
                return

            success = await self.bot.db.remove_birthday(interaction.guild.id, user.id)

            if success:
                embed = EmbedFactory.success_embed(
                    "Geburtstag entfernt",
                    f"Der Geburtstag von {user.display_name} wurde erfolgreich entfernt.",
                )
            else:
                embed = EmbedFactory.error_embed(
                    "Fehler",
                    "Der Geburtstag konnte nicht entfernt werden.",
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Geburtstags: {e}")
            embed = EmbedFactory.unexpected_error_embed("Entfernen des Geburtstags")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _handle_show_birthday(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
    ):
        """Behandelt die Anzeige eines Geburtstags"""
        if not interaction.guild:
            return

        try:
            birthday = await self.bot.db.get_birthday(interaction.guild.id, user.id)

            if not birthday:
                embed = EmbedFactory.error_embed(
                    "Kein Geburtstag gefunden",
                    f"Es ist kein Geburtstag für {user.display_name} gespeichert.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Formatiere das Datum
            date_str = (
                f"{birthday.birth_day}. {GERMAN_MONTH_NAMES[birthday.birth_month]}"
            )

            embed = EmbedFactory.info_embed(
                "Geburtstag",
                f"**{user.display_name}** hat am **{date_str}** Geburtstag.",
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Geburtstags: {e}")
            embed = EmbedFactory.unexpected_error_embed("Laden des Geburtstags")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _handle_list_birthdays(self, interaction: discord.Interaction):
        """Behandelt die Anzeige aller Geburtstage"""
        if not interaction.guild:
            return

        try:
            birthdays = await self.bot.db.get_guild_birthdays(interaction.guild.id)

            if not birthdays:
                embed = EmbedFactory.error_embed(
                    "Keine Geburtstage",
                    "Es sind noch keine Geburtstage in diesem Server gespeichert.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Formatiere die Geburtstage

            birthday_list = []
            for birthday in birthdays:
                # Versuche zuerst den Benutzer als Server-Member zu finden
                user = interaction.guild.get_member(birthday.user_id)

                if not user:
                    # Falls nicht im Server, versuche den Benutzer über die API zu holen
                    try:
                        user = await self.bot.fetch_user(birthday.user_id)
                    except (discord.NotFound, discord.HTTPException):
                        # Benutzer existiert nicht mehr, überspringe
                        continue

                date_str = (
                    f"{birthday.birth_day}. {GERMAN_MONTH_NAMES[birthday.birth_month]}"
                )
                # Kennzeichne offline Benutzer
                if isinstance(user, discord.Member):
                    birthday_list.append(f"**{user.display_name}**: {date_str}")
                else:
                    birthday_list.append(
                        f"**{user.display_name}** (offline): {date_str}"
                    )

            if not birthday_list:
                embed = EmbedFactory.error_embed(
                    "Keine Geburtstage",
                    "Alle gespeicherten Geburtstage gehören zu Benutzern, die nicht mehr existieren.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Teile die Liste auf, wenn sie zu lang ist
            description = "\n".join(birthday_list)
            if len(description) > MAX_EMBED_DESCRIPTION_LENGTH:
                description = description[:MAX_EMBED_DESCRIPTION_LENGTH] + "\n..."

            embed = EmbedFactory.info_embed(
                "Geburtstage in diesem Server",
                description,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Geburtstage: {e}")
            embed = EmbedFactory.unexpected_error_embed("Laden der Geburtstage")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def save_birthday_from_string(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
        birthday_str: str,
    ):
        """Speichert den Geburtstag aus einem String im Format DD.MM."""
        if not interaction.guild:
            return

        try:
            # Parse das Datum im Format DD.MM.
            if not birthday_str.endswith("."):
                birthday_str += "."

            if birthday_str.count(".") != DOT_COUNT_IN_DATE:
                embed = EmbedFactory.error_embed(
                    "Ungültiges Format",
                    "Bitte verwende das Format DD.MM. (z.B. 25.12.)",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            parts = birthday_str.strip(".").split(".")
            if len(parts) != DATE_PARTS:
                embed = EmbedFactory.error_embed(
                    "Ungültiges Format",
                    "Bitte verwende das Format DD.MM. (z.B. 25.12.)",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                day = int(parts[0])
                month = int(parts[1])
            except ValueError:
                embed = EmbedFactory.error_embed(
                    "Ungültige Zahlen",
                    "Tag und Monat müssen Zahlen sein.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Validiere Tag und Monat
            if not (MIN_MONTH <= month <= MAX_MONTH):
                embed = EmbedFactory.error_embed(
                    "Ungültiger Monat",
                    f"Der Monat muss zwischen {MIN_MONTH} und {MAX_MONTH} liegen.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if not (MIN_DAY <= day <= MAX_DAY):
                embed = EmbedFactory.error_embed(
                    "Ungültiger Tag",
                    f"Der Tag muss zwischen {MIN_DAY} und {MAX_DAY} liegen.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Überprüfe auf gültige Tag/Monat-Kombination
            try:
                # Verwende das aktuelle Jahr für die Validierung
                current_year = date.today().year
                days_in_month = calendar.monthrange(current_year, month)[1]
                if day > days_in_month:
                    embed = EmbedFactory.error_embed(
                        "Ungültiges Datum",
                        f"Der {month}. Monat hat nur {days_in_month} Tage.",
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            except ValueError:
                embed = EmbedFactory.error_embed(
                    "Ungültiges Datum",
                    "Das angegebene Datum ist nicht gültig.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Erstelle Birthday-Objekt
            birthday = Birthday(
                id=None,
                guild_id=interaction.guild.id,
                user_id=user.id,
                birth_day=day,
                birth_month=month,
            )

            success = await self.bot.db.add_birthday(birthday)

            if success:
                # Formatiere das Datum für die Anzeige
                date_str = f"{day}. {GERMAN_MONTH_NAMES[month]}"

                embed = EmbedFactory.success_embed(
                    "Geburtstag gespeichert",
                    f"Der Geburtstag von {user.display_name} wurde auf den **{date_str}** gesetzt.",
                )
            else:
                embed = EmbedFactory.error_embed(
                    "Fehler",
                    "Der Geburtstag konnte nicht gespeichert werden.",
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Geburtstags: {e}")
            embed = EmbedFactory.unexpected_error_embed("Speichern des Geburtstags")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Admin Testing Commands

    @commands.hybrid_command(name="birthday_test")
    @commands.has_permissions(administrator=True)
    @track_command_usage
    async def test_birthday_notifications(self, ctx):
        """Testet die Geburtstags-Benachrichtigungen manuell für diesen Server (nur für Admins)"""
        if not ctx.guild:
            await ctx.send("Dieser Befehl kann nur in einem Server verwendet werden.")
            return

        try:
            await ctx.send(
                f"Teste Geburtstags-Benachrichtigungen für {ctx.guild.name}..."
            )

            # Hole nur Geburtstage für heute in diesem Server
            today_birthdays = await self.bot.db.get_birthdays_today()
            guild_birthdays = [b for b in today_birthdays if b.guild_id == ctx.guild.id]

            if not guild_birthdays:
                await ctx.send("Keine Geburtstage heute in diesem Server gefunden.")
                return

            logger.info(
                f"Test: Gefunden {len(guild_birthdays)} Geburtstage heute in {ctx.guild.name}"
            )

            # Sende Benachrichtigungen nur für diesen Server
            await self._send_birthday_notifications(ctx.guild.id, guild_birthdays)

            await ctx.send(
                f"Test der Geburtstags-Benachrichtigungen für {ctx.guild.name} abgeschlossen."
            )

        except Exception as e:
            logger.error(
                f"Fehler beim Testen der Geburtstags-Benachrichtigungen: {e}",
                exc_info=True,
            )
            await ctx.send(f"Fehler beim Testen: {str(e)}")

    @commands.hybrid_command(name="birthday_status")
    @commands.has_permissions(administrator=True)
    @track_command_usage
    async def birthday_task_status(self, ctx):
        """Zeigt den Status der Geburtstags-Task an (nur für Admins)"""
        try:
            status = "Läuft" if self.daily_birthday_check.is_running() else "Gestoppt"
            next_iteration = self.daily_birthday_check.next_iteration

            embed = EmbedFactory.info_embed(
                "Geburtstags-Task Status",
                "",
            )
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(
                name="Nächste Ausführung",
                value=f"<t:{int(next_iteration.timestamp())}:F>"
                if next_iteration
                else "Unbekannt",
                inline=True,
            )
            embed.add_field(
                name="Ausführungszeit", value="Täglich um 9:00 Uhr", inline=False
            )

            # Zeige auch Server-spezifische Informationen
            if ctx.guild:
                today_birthdays = await self.bot.db.get_birthdays_today()
                guild_birthdays = [
                    b for b in today_birthdays if b.guild_id == ctx.guild.id
                ]
                embed.add_field(
                    name=f"Geburtstage heute in {ctx.guild.name}",
                    value=f"{len(guild_birthdays)} gefunden",
                    inline=False,
                )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Task-Status: {e}", exc_info=True)
            await ctx.send(f"Fehler beim Anzeigen des Status: {str(e)}")


@app_commands.context_menu(name="Geburtstag setzen")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guild_only()
async def set_birthday_context_menu(
    interaction: discord.Interaction, user: discord.Member
):
    """Kontextmenü-Befehl zum Setzen des Geburtstags eines Benutzers"""

    # Öffne das Modal für die Geburtstags-Eingabe
    modal = BirthdayModal(user)
    await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
    bot.tree.add_command(set_birthday_context_menu)
