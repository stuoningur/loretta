"""
Spezifikationskommandos für Hardware-Specs der Benutzer
"""

import logging
import time
from typing import Dict, Optional, Tuple, Union

import discord
from discord import app_commands
from discord.ext import commands

from src.bot.utils.decorators import track_command_usage, validate_input
from src.bot.utils.embeds import EmbedFactory
from src.bot.utils.pagination import SearchPaginationView
from src.bot.utils.user_resolver import UserResolver
from src.database import Specification

# Konstanten
MAX_SPECS_LENGTH = 2000
MAX_SEARCH_RESULTS = 2  # Ergebnisse pro Seite
MAX_SEARCH_PAGES = 10  # Maximale Seiten um Missbrauch zu verhindern
CACHE_TTL = 300  # Cache-Lebensdauer in Sekunden (5 Minuten)

logger = logging.getLogger(__name__)


class Specs(commands.Cog):
    """Cog für Hardware-Spezifikationen der Benutzer"""

    def __init__(self, bot):
        self.bot = bot
        # Einfacher In-Memory-Cache für Suchergebnisse
        # Format: {(guild_id, search_term, page): (results, total_count, timestamp)}
        self._search_cache: Dict[Tuple[int, str, int], Tuple[list, int, float]] = {}

    def _get_cache_key(
        self, guild_id: int, search_term: str, page: int
    ) -> Tuple[int, str, int]:
        """Generiere Cache-Schlüssel für Suchergebnisse"""
        return (guild_id, search_term.lower().strip(), page)

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Prüfe ob Cache-Eintrag noch gültig ist"""
        return time.time() - timestamp < CACHE_TTL

    def _cleanup_cache(self):
        """Entferne abgelaufene Cache-Einträge"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, _, timestamp) in self._search_cache.items()
            if current_time - timestamp >= CACHE_TTL
        ]
        for key in expired_keys:
            del self._search_cache[key]

    async def _get_cached_search_results(
        self, guild_id: int, search_term: str, limit: int, offset: int
    ) -> Tuple[list, int]:
        """Hole Suchergebnisse aus Cache oder Datenbank"""
        page = offset // limit
        cache_key = self._get_cache_key(guild_id, search_term, page)

        # Prüfe zuerst den Cache
        if cache_key in self._search_cache:
            results, total_count, timestamp = self._search_cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Cache hit for search: {search_term} (page {page})")
                return results, total_count
            else:
                # Entferne abgelaufenen Eintrag
                del self._search_cache[cache_key]

        # Cache-Miss - lade aus Datenbank
        logger.debug(f"Cache miss for search: {search_term} (page {page})")
        results, total_count = await self.bot.db.search_specifications(
            guild_id, search_term, limit, offset
        )

        # Cache die Ergebnisse
        self._search_cache[cache_key] = (results, total_count, time.time())

        # Bereinige alte Cache-Einträge periodisch
        if (
            len(self._search_cache) > 100
        ):  # Willkürliches Limit um Memory-Bloat zu verhindern
            self._cleanup_cache()

        return results, total_count

    def _invalidate_guild_cache(self, guild_id: int):
        """Invalidiere alle Cache-Einträge für eine bestimmte Guild"""
        keys_to_remove = [
            key for key in self._search_cache.keys() if key[0] == guild_id
        ]
        for key in keys_to_remove:
            del self._search_cache[key]

    @commands.hybrid_group(
        name="specs",
        aliases=["s"],
        invoke_without_command=True,
        description="Hardware-Spezifikationen verwalten und anzeigen",
    )
    @commands.guild_only()
    @track_command_usage
    async def specs(self, ctx: commands.Context, *, user: Optional[str] = None):
        """Hardware-Spezifikationen verwalten und anzeigen"""
        # Zeige Spezifikationen für den angegebenen Benutzer oder den Autor
        target_user = ctx.author
        if user:
            target_user = await UserResolver.resolve_user(ctx, user)
            if not target_user:
                return

        await self.show_specifications_ctx(ctx, target_user)

    @specs.command(name="show")
    @commands.guild_only()
    @track_command_usage
    async def specs_show(self, ctx: commands.Context, *, user: Optional[str] = None):
        """Zeige Spezifikationen eines Benutzers an"""
        target_user = ctx.author
        if user:
            target_user = await UserResolver.resolve_user(ctx, user)
            if not target_user:
                return

        await self.show_specifications_ctx(ctx, target_user)

    def _validate_specs_text(self, specs_text: str) -> Optional[str]:
        """Validiere Spezifikationstext-Eingabe

        Args:
            specs_text: Der zu validierende Spezifikationstext

        Returns:
            Fehlermeldung bei Validierungsfehlern, None wenn gültig
        """
        if not specs_text or not specs_text.strip():
            return "Die Spezifikationen dürfen nicht leer sein."

        specs_text = specs_text.strip()

        if len(specs_text) > MAX_SPECS_LENGTH:
            return f"Die Spezifikationen dürfen maximal {MAX_SPECS_LENGTH} Zeichen lang sein. Deine Eingabe hat {len(specs_text)} Zeichen."

        if len(specs_text) < 10:
            return "Die Spezifikationen sollten mindestens 10 Zeichen lang sein."

        # Prüfe auf potentiell problematischen Inhalt
        suspicious_patterns = ["<@", "<#", "@everyone", "@here"]
        if any(pattern in specs_text.lower() for pattern in suspicious_patterns):
            return "Die Spezifikationen dürfen keine Mentions oder Channel-Verlinkungen enthalten."

        return None

    @specs.command(name="set")
    @commands.guild_only()
    @validate_input(
        min_length=10, max_length=MAX_SPECS_LENGTH, field_name="Spezifikationen"
    )
    @track_command_usage
    async def specs_set(self, ctx: commands.Context, *, specs_text: str):
        """Setze deine Hardware-Spezifikationen"""
        # Zusätzliche Validierung für Spezifikationen
        validation_error = self._validate_specs_text(specs_text)
        if validation_error:
            embed = EmbedFactory.error_embed("Ungültige Eingabe", validation_error)
            await ctx.send(embed=embed)
            return

        # Bereinige die Eingabe
        specs_text = specs_text.strip()

        try:
            if not ctx.guild:
                return
            # Prüfe ob bereits Spezifikationen existieren
            existing_spec = await self.bot.db.get_specification(
                ctx.guild.id, ctx.author.id
            )
            is_update = existing_spec is not None

            # Erstelle Specification-Objekt
            specification = Specification(
                id=None,
                guild_id=ctx.guild.id,
                user_id=ctx.author.id,
                specs_text=specs_text,
            )

            success = await self.bot.db.add_specification(
                specification, ctx.author, ctx.guild
            )

            if success:
                # Invalidiere Suchcache für diese Guild da sich Spezifikationen geändert haben
                self._invalidate_guild_cache(ctx.guild.id)
                embed = EmbedFactory.success_embed(
                    "Erfolgreich gespeichert",
                    "Deine Spezifikationen wurden aktualisiert!"
                    if is_update
                    else "Deine Spezifikationen sind jetzt registriert!",
                )
                embed.add_field(
                    name="Zeichenanzahl",
                    value=f"{len(specs_text)} / {MAX_SPECS_LENGTH}",
                    inline=True,
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedFactory.database_error_embed(
                    "Speichern der Spezifikationen"
                )
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(
                f"Fehler beim Speichern der Spezifikationen für Benutzer {ctx.author.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Speichern der Spezifikationen")
            await ctx.send(embed=embed)

    @specs.command(name="delete")
    @commands.guild_only()
    @track_command_usage
    async def specs_delete(self, ctx: commands.Context):
        """Lösche deine Hardware-Spezifikationen"""
        try:
            if not ctx.guild:
                return
            specification = await self.bot.db.get_specification(
                ctx.guild.id, ctx.author.id
            )

            if not specification:
                embed = EmbedFactory.error_embed(
                    "Keine Spezifikationen",
                    "Du hast keine Spezifikationen registriert.",
                )
                await ctx.send(embed=embed)
                return

            success = await self.bot.db.remove_specification(
                ctx.guild.id, ctx.author.id, ctx.author, ctx.guild
            )

            if success:
                # Invalidiere Suchcache für diese Guild da sich Spezifikationen geändert haben
                self._invalidate_guild_cache(ctx.guild.id)
                embed = EmbedFactory.success_embed(
                    "Erfolgreich gelöscht", "Deine Spezifikationen wurden gelöscht!"
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedFactory.database_error_embed("Löschen der Spezifikationen")
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(
                f"Fehler beim Löschen der Spezifikationen für Benutzer {ctx.author.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Löschen der Spezifikationen")
            await ctx.send(embed=embed)

    @specs.command(name="raw")
    @commands.guild_only()
    @track_command_usage
    async def specs_raw(self, ctx: commands.Context):
        """Zeige deine Spezifikationen als Raw-Text an"""
        try:
            if not ctx.guild:
                return
            specification = await self.bot.db.get_specification(
                ctx.guild.id, ctx.author.id
            )

            if not specification:
                embed = EmbedFactory.error_embed(
                    "Keine Spezifikationen",
                    "Du hast keine Spezifikationen registriert.",
                )
                await ctx.send(embed=embed)
                return

            # Sende als Code-Block für bessere Lesbarkeit
            raw_text = f"```\n{specification.specs_text}\n```"

            if len(raw_text) > 2000:
                # Falls zu lang, kürze den Text
                max_content = 2000 - 10  # Reserve für ```\n...\n```
                truncated_text = specification.specs_text[: max_content - 3] + "..."
                raw_text = f"```\n{truncated_text}\n```"

            await ctx.send(raw_text)

        except Exception as e:
            logger.error(
                f"Fehler beim Anzeigen der Raw-Spezifikationen für Benutzer {ctx.author.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Laden der Spezifikationen")
            await ctx.send(embed=embed)

    @specs.command(name="search")
    @commands.guild_only()
    @validate_input(min_length=2, max_length=100, field_name="Suchbegriff")
    @track_command_usage
    async def specs_search(self, ctx: commands.Context, *, search_term: str):
        """Suche nach Hardware in allen Spezifikationen"""
        try:
            if not ctx.guild:
                return
            guild_id = ctx.guild.id

            # Erstelle Suchfunktion für Paginierung
            async def search_function(limit: int, offset: int):
                return await self._get_cached_search_results(
                    guild_id, search_term, limit, offset
                )

            # Erstelle Paginierungsansicht und hole erste Seite
            view = SearchPaginationView(
                search_function, ctx.guild, search_term, ctx.author, MAX_SEARCH_RESULTS
            )
            embed = await view.get_page_embed(0)
            await view.update_buttons()

            # Sende mit Paginierung wenn mehrere Seiten, sonst nur das Embed
            if view.total_pages > 1:
                message = await ctx.send(embed=embed, view=view)
                # Speichere Nachrichtenreferenz für Timeout-Behandlung
                view.message = message
            else:
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(
                f"Fehler im Suchbefehl für Begriff '{search_term}': {e}", exc_info=True
            )
            embed = EmbedFactory.error_embed(
                "Suchfehler",
                "Es ist ein Fehler bei der Suche aufgetreten. Bitte versuche es später erneut.",
            )
            await ctx.send(embed=embed)

    @specs.command(name="clean")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @track_command_usage
    async def specs_clean(self, ctx: commands.Context):
        """Bereinige die Spezifikations-Datenbank von Benutzern, die nicht mehr im Server sind"""

        try:
            # Defer für Slash-Commands, da die Operation Zeit brauchen kann
            if ctx.interaction:
                await ctx.defer(ephemeral=True)

            # Hole alle Spezifikationen für diese Guild
            if not ctx.guild:
                embed = EmbedFactory.error_embed(
                    "Fehler", "Dieser Befehl kann nur in einem Server verwendet werden."
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return

            all_specs = await self.bot.db.get_all_guild_specifications(ctx.guild.id)  # type: ignore

            if not all_specs:
                embed = EmbedFactory.info_embed(
                    "Keine Einträge",
                    "Es wurden keine Spezifikationseinträge in der Datenbank gefunden.",
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return

            # Identifiziere Benutzer, die nicht mehr im Server sind
            users_to_remove = []
            for spec in all_specs:
                if not ctx.guild:
                    continue
                member = ctx.guild.get_member(spec.user_id)
                if member is None:
                    users_to_remove.append(spec)

            if not users_to_remove:
                embed = EmbedFactory.success_embed(
                    "Datenbank ist sauber",
                    "Alle Spezifikationseinträge gehören zu aktiven Servermitgliedern.",
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return

            # Lösche die Einträge inaktiver Benutzer
            removed_count = 0
            for spec in users_to_remove:
                if not ctx.guild:
                    continue
                success = await self.bot.db.remove_specification(
                    ctx.guild.id, spec.user_id, None, ctx.guild
                )
                if success:
                    removed_count += 1

            # Erstelle Erfolgsmeldung
            embed = EmbedFactory.success_embed(
                "Datenbank bereinigt",
                f"{removed_count} von {len(users_to_remove)} Spezifikationseinträgen wurden erfolgreich entfernt.",
            )

            embed.add_field(
                name="Entfernte Einträge",
                value=f"{removed_count} Einträge von Benutzern, die nicht mehr im Server sind",
                inline=False,
            )

            embed.add_field(
                name="Verbleibende Einträge",
                value=f"{len(all_specs) - removed_count} aktive Spezifikationseinträge",
                inline=False,
            )

            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)

            logger.info(
                f"Database cleanup performed by {ctx.author} in guild {ctx.guild.name if ctx.guild else 'Unknown'}: "
                f"{removed_count} specifications removed"
            )

        except Exception as e:
            logger.error(f"Fehler während Datenbank-Bereinigung: {e}")
            embed = EmbedFactory.error_embed(
                "Fehler", "Es ist ein Fehler beim Bereinigen der Datenbank aufgetreten."
            )
            if ctx.interaction and ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)

    def _create_specifications_embed(
        self,
        specification: Optional[Specification],
        target_user: Union[discord.Member, discord.User],
        requester: Union[discord.Member, discord.User],
    ) -> discord.Embed:
        """Erstelle Embed für Anzeige von Spezifikationen"""
        if not specification:
            return EmbedFactory.no_specs_embed(target_user)

        return EmbedFactory.specs_embed(
            target_user, specification.specs_text, requester, specification.updated_at
        )

    async def show_specifications_ctx(
        self,
        ctx: commands.Context,
        user: Union[discord.Member, discord.User],
    ):
        """Zeige Spezifikationen für einen Benutzer an (Context-Version)"""
        if not ctx.guild:
            return

        try:
            specification = await self.bot.db.get_specification(ctx.guild.id, user.id)
            embed = self._create_specifications_embed(specification, user, ctx.author)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(
                f"Fehler beim Anzeigen der Spezifikationen für Benutzer {user.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Laden der Spezifikationen")
            await ctx.send(embed=embed)

    async def show_specifications_interaction(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
    ):
        """Zeige Spezifikationen für einen Benutzer an (Interaction-Version)"""
        if not interaction.guild:
            return

        try:
            specification = await self.bot.db.get_specification(
                interaction.guild.id, user.id
            )
            embed = self._create_specifications_embed(
                specification, user, interaction.user
            )

            # Sende als ephemeral wenn keine Specs gefunden, sonst öffentlich
            ephemeral = specification is None
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

        except Exception as e:
            logger.error(
                f"Fehler beim Anzeigen der Spezifikationen für Benutzer {user.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Laden der Spezifikationen")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    def parse_timestamp(self, timestamp_str: str) -> float:
        """Parse SQLite Zeitstempel-String zu Unix-Zeitstempel"""
        try:
            from datetime import datetime, timezone

            # SQLite CURRENT_TIMESTAMP Format: "YYYY-MM-DD HH:MM:SS" in UTC
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            # SQLite Zeitstempel sind in UTC, daher müssen wir die Zeitzone setzen
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception as e:
            logger.error(f"Fehler beim Parsen des Zeitstempels {timestamp_str}: {e}")
            return 0


@app_commands.guild_only()
@app_commands.context_menu(name="Spezifikationen anzeigen")
async def show_user_specs_context(
    interaction: discord.Interaction, user: discord.Member
):
    """Zeigt die Hardware-Spezifikationen eines Benutzers über das Kontextmenü an"""
    if interaction.guild:
        try:
            # Hole die Spezifikationen aus der Datenbank
            from bot.main import LorettaBot

            if not isinstance(interaction.client, LorettaBot):
                embed = EmbedFactory.error_embed(
                    "Fehler", "Bot-Instanz nicht verfügbar."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            specification = await interaction.client.db.get_specification(
                interaction.guild.id, user.id
            )

            # Hole die Cog-Instanz um die Embed-Erstellungsmethode zu verwenden
            cog = interaction.client.get_cog("Specs")
            if not cog or not isinstance(cog, Specs):
                return
            if cog and isinstance(cog, Specs):
                embed = cog._create_specifications_embed(
                    specification, user, interaction.user
                )
                ephemeral = specification is None
                await interaction.response.send_message(
                    embed=embed, ephemeral=ephemeral
                )
            else:
                embed = EmbedFactory.error_embed(
                    "Systemfehler", "Spezifikations-Cog nicht verfügbar."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            logger.info(
                f"Context menu specs request by {interaction.user} for {user} in guild {interaction.guild.name}"
            )

        except Exception as e:
            logger.error(
                f"Fehler im Kontextmenü-Specs-Befehl für Benutzer {user.id}: {e}"
            )
            embed = EmbedFactory.unexpected_error_embed("Laden der Spezifikationen")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Specs(bot))

    # Füge das Kontext-Menü zum Command Tree hinzu
    bot.tree.add_command(show_user_specs_context)
