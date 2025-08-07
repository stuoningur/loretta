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

logger = logging.getLogger(__name__)


class BirthdayModal(discord.ui.Modal):
    """Modal für Geburtsdatums-Eingabe"""

    def __init__(self, user: Union[discord.Member, discord.User]):
        super().__init__(title=f"Geburtstag für {user.display_name}")
        self.user = user

        self.birthday_input = discord.ui.TextInput(
            label="Geburtsdatum",
            placeholder="Format: DD.MM. (z.B. 25.12.)",
            max_length=6,
            min_length=5,
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

    @tasks.loop(time=time(hour=9, minute=0, second=0))  # 9:00 Uhr täglich
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

            # Hole die konfigurierten Geburtstags-Kanäle für diese Guild
            birthday_channels = await self.bot.db.get_birthday_channels(guild_id)

            if not birthday_channels:
                logger.info(
                    f"Keine Geburtstags-Kanäle für Guild {guild.name} konfiguriert"
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

            # Sende Nachrichten in alle konfigurierten Kanäle
            for channel_id in birthday_channels:
                channel = guild.get_channel(channel_id)
                if not channel:
                    logger.warning(
                        f"Geburtstags-Kanal {channel_id} in Guild {guild.name} nicht gefunden"
                    )
                    continue

                # Überprüfe Bot-Berechtigungen
                if not channel.permissions_for(guild.me).send_messages:
                    logger.warning(
                        f"Keine Berechtigung zum Senden in Kanal {channel.name} in Guild {guild.name}"
                    )
                    continue

                await self._send_birthday_message(channel, birthday_users)

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
            if len(birthday_users) == 1:
                # Einzelner Geburtstag
                member, _ = birthday_users[0]

                # Wähle eine zufällige Nachricht
                import random

                message_template = random.choice(self.birthday_messages)
                message = message_template.format(user=member.mention)

                # Erstelle Embed
                embed = discord.Embed(
                    title="🎉 Geburtstag! 🎂",
                    description=message,
                    color=discord.Color.gold(),
                )

                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="🎈 Hab einen wunderschönen Tag! 🎈")

                await channel.send(embed=embed)

            else:
                # Mehrere Geburtstage
                user_mentions = [member.mention for member, _ in birthday_users]

                # Erstelle Embed für mehrere Geburtstage
                embed = discord.Embed(
                    title="🎉 Mehrere Geburtstage heute! 🎂",
                    description="🎈 Herzlichen Glückwunsch an:\n"
                    + "\n".join(user_mentions),
                    color=discord.Color.gold(),
                )

                embed.set_footer(text="🎉 Feiert schön zusammen! 🎉")

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

    @app_commands.command(
        name="geburtstag",
        description="Verwalte Geburtstage - hinzufügen, entfernen oder anzeigen",
    )
    @app_commands.describe(
        aktion="Was möchtest du tun?",
        benutzer="Benutzer für den die Aktion ausgeführt werden soll (nur für Admins)",
        benutzer_id="Discord User ID für offline Benutzer (nur für Admins)",
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
        benutzer: Optional[discord.Member] = None,
        benutzer_id: Optional[str] = None,
    ):
        """Hauptkommando für Geburtstage"""
        if not interaction.guild:
            embed = discord.Embed(
                title="Fehler",
                description="Dieser Befehl kann nur in einem Server verwendet werden.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validiere Parameter
        if benutzer and benutzer_id:
            embed = discord.Embed(
                title="Fehler",
                description="Du kannst nicht sowohl einen Benutzer als auch eine Benutzer-ID angeben.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Bestimme den Zielbenutzer
        target_user = None
        is_admin_action = False

        if benutzer_id:
            # Versuche User ID zu validieren und zu konvertieren
            try:
                user_id = int(benutzer_id)
                target_user = await self.bot.fetch_user(user_id)
                is_admin_action = True
            except (ValueError, discord.NotFound, discord.HTTPException):
                embed = discord.Embed(
                    title="Ungültige Benutzer-ID",
                    description="Die angegebene Benutzer-ID ist ungültig oder der Benutzer existiert nicht.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        elif benutzer:
            target_user = benutzer
            is_admin_action = benutzer != interaction.user
        else:
            target_user = interaction.user

        # Nur Administratoren können Geburtstage für andere Benutzer verwalten
        if is_admin_action:
            member = interaction.guild.get_member(interaction.user.id)
            if not member or not member.guild_permissions.administrator:
                embed = discord.Embed(
                    title="Keine Berechtigung",
                    description="Du benötigst Administrator-Rechte, um Geburtstage für andere Benutzer zu verwalten.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
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
                embed = discord.Embed(
                    title="Kein Geburtstag gefunden",
                    description=f"Es ist kein Geburtstag für {user.display_name} gespeichert.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            success = await self.bot.db.remove_birthday(interaction.guild.id, user.id)

            if success:
                embed = discord.Embed(
                    title="Geburtstag entfernt",
                    description=f"Der Geburtstag von {user.display_name} wurde erfolgreich entfernt.",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Der Geburtstag konnte nicht entfernt werden.",
                    color=discord.Color.red(),
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Geburtstags: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Entfernen des Geburtstags aufgetreten.",
                color=discord.Color.red(),
            )
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
                embed = discord.Embed(
                    title="Kein Geburtstag gefunden",
                    description=f"Es ist kein Geburtstag für {user.display_name} gespeichert.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Formatiere das Datum
            date_str = (
                f"{birthday.birth_day}. {GERMAN_MONTH_NAMES[birthday.birth_month]}"
            )

            embed = discord.Embed(
                title="Geburtstag",
                description=f"**{user.display_name}** hat am **{date_str}** Geburtstag.",
                color=discord.Color.blurple(),
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Geburtstags: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Laden des Geburtstags aufgetreten.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _handle_list_birthdays(self, interaction: discord.Interaction):
        """Behandelt die Anzeige aller Geburtstage"""
        if not interaction.guild:
            return

        try:
            birthdays = await self.bot.db.get_guild_birthdays(interaction.guild.id)

            if not birthdays:
                embed = discord.Embed(
                    title="Keine Geburtstage",
                    description="Es sind noch keine Geburtstage in diesem Server gespeichert.",
                    color=discord.Color.red(),
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
                embed = discord.Embed(
                    title="Keine Geburtstage",
                    description="Alle gespeicherten Geburtstage gehören zu Benutzern, die nicht mehr existieren.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Teile die Liste auf, wenn sie zu lang ist
            description = "\n".join(birthday_list)
            if len(description) > 4000:
                description = description[:4000] + "\n..."

            embed = discord.Embed(
                title="Geburtstage in diesem Server",
                description=description,
                color=discord.Color.blurple(),
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Geburtstage: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Laden der Geburtstage aufgetreten.",
                color=discord.Color.red(),
            )
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

            if birthday_str.count(".") != 2:
                embed = discord.Embed(
                    title="Ungültiges Format",
                    description="Bitte verwende das Format DD.MM. (z.B. 25.12.)",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            parts = birthday_str.strip(".").split(".")
            if len(parts) != 2:
                embed = discord.Embed(
                    title="Ungültiges Format",
                    description="Bitte verwende das Format DD.MM. (z.B. 25.12.)",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                day = int(parts[0])
                month = int(parts[1])
            except ValueError:
                embed = discord.Embed(
                    title="Ungültige Zahlen",
                    description="Tag und Monat müssen Zahlen sein.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Validiere Tag und Monat
            if not (1 <= month <= 12):
                embed = discord.Embed(
                    title="Ungültiger Monat",
                    description="Der Monat muss zwischen 1 und 12 liegen.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if not (1 <= day <= 31):
                embed = discord.Embed(
                    title="Ungültiger Tag",
                    description="Der Tag muss zwischen 1 und 31 liegen.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Überprüfe auf gültige Tag/Monat-Kombination
            try:
                # Verwende das aktuelle Jahr für die Validierung
                current_year = date.today().year
                days_in_month = calendar.monthrange(current_year, month)[1]
                if day > days_in_month:
                    embed = discord.Embed(
                        title="Ungültiges Datum",
                        description=f"Der {month}. Monat hat nur {days_in_month} Tage.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            except ValueError:
                embed = discord.Embed(
                    title="Ungültiges Datum",
                    description="Das angegebene Datum ist nicht gültig.",
                    color=discord.Color.red(),
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

                embed = discord.Embed(
                    title="Geburtstag gespeichert",
                    description=f"Der Geburtstag von {user.display_name} wurde auf den **{date_str}** gesetzt.",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Der Geburtstag konnte nicht gespeichert werden.",
                    color=discord.Color.red(),
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Geburtstags: {e}")
            embed = discord.Embed(
                title="Fehler",
                description="Es ist ein Fehler beim Speichern des Geburtstags aufgetreten.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Admin Testing Commands

    @commands.hybrid_command(name="test_birthday")
    @commands.has_permissions(administrator=True)
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
    async def birthday_task_status(self, ctx):
        """Zeigt den Status der Geburtstags-Task an (nur für Admins)"""
        try:
            status = "Läuft" if self.daily_birthday_check.is_running() else "Gestoppt"
            next_iteration = self.daily_birthday_check.next_iteration

            embed = discord.Embed(
                title="Geburtstags-Task Status",
                color=discord.Color.blurple(),
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


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
