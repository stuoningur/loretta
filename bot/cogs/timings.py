"""
Memory Timings Cog für Loretta Bot
Enthält Kommandos für Memory-Timing-Suche aus der Datenbank mit Dropdown-Interface
"""

import logging
import re
from typing import Any, Dict, List

import discord
from discord.ext import commands

from bot.utils.decorators import track_command_usage
from bot.utils.embeds import EmbedFactory
from database import MemoryTiming

logger = logging.getLogger(__name__)


def has_value(value) -> bool:
    """Check if a value is not null/empty and should be displayed"""
    if value is None or value == "" or str(value).lower() in ["null", "none", "n/a"]:
        return False
    return True


def format_timing_value(value) -> str:
    """Format timing values for display"""
    return str(value)


class GenerationSelect(discord.ui.Select):
    """Dropdown für Generation-Auswahl"""

    def __init__(self, generations: List[str], bot):
        self.bot = bot
        options = []
        for gen in generations:
            # Kapitalisiere Generation und teile bei Zahlen auf
            if gen.lower().startswith("zen"):
                # Teile zen1, zen2, zen4 etc. in "Zen 1", "Zen 2", "Zen 4"
                parts = re.split(r"(\d+)", gen.lower())
                display_parts = []
                for part in parts:
                    if part.isdigit():
                        display_parts.append(part)
                    elif part:
                        display_parts.append(part.capitalize())
                display_name = " ".join(display_parts)
            else:
                display_name = gen.title()

            options.append(
                discord.SelectOption(
                    label=display_name,
                    value=gen,
                    description=f"CPU Generation {display_name}",
                )
            )

        super().__init__(
            placeholder="Wähle eine CPU-Generation aus...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle generation selection"""
        generation = self.values[0]

        # Hole verfügbare Presets für diese Generation
        timings = await self.bot.db.search_memory_timings(
            generation=generation, limit=1000
        )

        if not timings:
            embed = EmbedFactory.error_embed(
                "Keine Presets gefunden",
                f"Keine Timing-Presets für Generation {generation} verfügbar.",
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Erstelle unique Preset-Liste (Name + Details für bessere Unterscheidung)
        preset_dict = {}
        for timing in timings:
            # Erstelle einen Preset-Key mit zusätzlichen Infos für Eindeutigkeit
            preset_key = f"{timing.name}"
            if timing.vendor and timing.ics and timing.memclk:
                display_name = (
                    f"{timing.name} ({timing.vendor} {timing.ics} {timing.memclk}MHz)"
                )
                preset_dict[preset_key] = {
                    "display_name": display_name,
                    "timing": timing,
                }

        if not preset_dict:
            embed = EmbedFactory.error_embed(
                "Keine Presets gefunden",
                f"Keine vollständigen Timing-Presets für Generation {generation} verfügbar.",
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Erstelle Preset-Auswahl-View
        view = PresetSelectionView(list(preset_dict.values()), generation)
        embed = discord.Embed(
            title="Preset auswählen",
            description=f"Wähle ein Timing-Preset für **{generation.upper()}** aus:",
            color=discord.Color.blurple(),
        )

        await interaction.response.edit_message(embed=embed, view=view)


class PresetSelect(discord.ui.Select):
    """Dropdown für Preset-Auswahl"""

    def __init__(self, presets: List[Dict[str, Any]], generation: str):
        self.generation = generation

        # Begrenze auf 25 Optionen (Discord Limit)
        limited_presets = presets[:25]

        options = []
        for i, preset_data in enumerate(limited_presets):
            timing = preset_data["timing"]
            display_name = preset_data["display_name"]

            # Kürze zu lange Namen
            if len(display_name) > 90:
                display_name = display_name[:87] + "..."

            options.append(
                discord.SelectOption(
                    label=display_name,
                    value=str(i),  # Index als Wert verwenden
                    description=f"Preset: {format_timing_value(timing.preset) if has_value(timing.preset) else 'Standard'}",
                )
            )

        super().__init__(
            placeholder="Wähle ein Timing-Preset aus...",
            min_values=1,
            max_values=1,
            options=options,
        )

        self.presets = limited_presets

    async def callback(self, interaction: discord.Interaction):
        """Handle preset selection"""
        try:
            preset_index = int(self.values[0])
            timing = self.presets[preset_index]["timing"]

            # Erstelle Timing-Embed
            embed = self._create_timing_embed(timing)

            await interaction.response.edit_message(embed=embed, view=None)

        except (ValueError, IndexError) as e:
            logger.error(f"Error in preset selection: {e}")
            embed = EmbedFactory.error_embed(
                "Auswahlfehler", "Es gab ein Problem bei der Preset-Auswahl."
            )
            await interaction.response.edit_message(embed=embed, view=None)

    def _create_timing_embed(self, timing: MemoryTiming) -> discord.Embed:
        """Erstelle dynamisches Timing-Embed - zeigt nur Daten an, die tatsächlich vorhanden sind"""
        embed = discord.Embed(
            title="Lorettas Timings",
            color=0xE74C3C,  # Rot wie im Original
        )

        # Preset Name - immer anzeigen
        preset_name = timing.name
        if has_value(timing.preset) and timing.preset:
            preset_name += f" {timing.preset.title()}"
        if has_value(timing.generation) and timing.generation:
            preset_name += f" {timing.generation.upper()}"

        embed.add_field(name="**Preset:**", value=f"**{preset_name}**", inline=False)

        # Taktraten - nur anzeigen wenn mindestens ein Wert vorhanden
        clock_settings = [
            ("MEMCLK", timing.memclk),
            ("FCLK", timing.fclk),
            ("PowerDownMode", timing.pdm),
            ("GearDownMode", timing.gdm),
        ]

        taktraten = []
        for name, value in clock_settings:
            if has_value(value):
                taktraten.append(f"{name:<13} {format_timing_value(value)}")

        if taktraten:
            embed.add_field(
                name="**Taktraten:**",
                value=f"```{chr(10).join(taktraten)}```",
                inline=False,
            )

        # Spannungen - nur anzeigen wenn mindestens ein Wert vorhanden
        voltage_settings = [
            ("VDIMM", timing.vdimm),
            ("VSOC", timing.vsoc),
            ("VDDG", timing.vddg),
            ("CLDO VDDP", timing.cldo_vddp),
            ("VDD", timing.vdd),
            ("VDDQ", timing.vddq),
            ("VDDIO", timing.vddio),
            ("VDDP", timing.vddp),
        ]

        spannungen = []
        for name, value in voltage_settings:
            if has_value(value):
                spannungen.append(f"{name:<12} {format_timing_value(value)}")

        if spannungen:
            embed.add_field(
                name="**Spannungen:**",
                value=f"```{chr(10).join(spannungen)}```",
                inline=False,
            )

        # Timings - dynamisch basierend auf verfügbaren Werten
        # Alle möglichen Timing-Parameter
        timing_params = [
            ("tCL", timing.tcl),
            ("tRCDRD", timing.trcdrp),
            ("tRCDWR", timing.trcdwr),
            ("tRCD", timing.trcd),  # Fallback falls trcdrp/trcdwr nicht vorhanden
            ("tRP", timing.trp),
            ("tRAS", timing.tras),
            ("tRC", timing.trc),
            ("tRRDS", timing.trrds),
            ("tRRDL", timing.trrdl),
            ("tFAW", timing.tfaw),
            ("tWTRS", timing.twtrs),
            ("tWTRL", timing.twtrl),
            ("tWR", timing.twr),
            ("tRDRDSCL", timing.trdrdscl),
            ("tWRWRSCL", timing.twrwrscl),
            ("tREFI", timing.trefi),
            ("tRFC", timing.trfc),
            ("tCWL", timing.tcwl),
            ("tRTP", timing.trtp),
            ("tRDWR", timing.trdwr),
            ("tWRRD", timing.twrrd),
            ("tWRWRSC", timing.twrwrsc),
            ("tWRWRSD", timing.twrwrsd),
            ("tWRWRDD", timing.twrwrdd),
            ("tRDRDSC", timing.trdrdsc),
            ("tRDRDSD", timing.trdrdsd),
            ("tRDRDDD", timing.trdrddd),
            ("tCKE", timing.tcke),
        ]

        # Filtere nur die Timings, die tatsächlich Werte haben
        available_timings = [
            (name, value) for name, value in timing_params if has_value(value)
        ]

        if available_timings:
            # Organisiere in zwei Spalten für bessere Darstellung
            timing_lines = []
            for i in range(0, len(available_timings), 2):
                left_name, left_val = available_timings[i]
                left_part = f"{left_name:<10} {format_timing_value(left_val):<6}"

                if i + 1 < len(available_timings):
                    right_name, right_val = available_timings[i + 1]
                    right_part = f"{right_name:<10} {format_timing_value(right_val)}"
                    timing_lines.append(f"{left_part} {right_part}")
                else:
                    timing_lines.append(left_part)

            embed.add_field(
                name="**Timings:**",
                value=f"```{chr(10).join(timing_lines)}```",
                inline=False,
            )

        # ProcODT - nur anzeigen wenn vorhanden
        if has_value(timing.procodt):
            embed.add_field(
                name="**ProcODT:**",
                value=f"```{format_timing_value(timing.procodt)}```",
                inline=False,
            )

        # RTTs - nur anzeigen wenn vorhanden
        if has_value(timing.rtts):
            rtts_display = format_timing_value(timing.rtts)
            # Versuche RTTs zu formatieren falls es mehrzeilig ist
            if "\n" in rtts_display or "," in rtts_display:
                lines = rtts_display.replace(",", "\n").split("\n")
                if len(lines) >= 2:
                    rtts_display = f"Single Rank  {lines[0].strip()}\nDual Rank    {lines[1].strip()}"

            embed.add_field(
                name="**RTTs:**", value=f"```{rtts_display}```", inline=False
            )

        # CADs - nur anzeigen wenn vorhanden
        if has_value(timing.cads):
            embed.add_field(
                name="**CADs:**",
                value=f"```{format_timing_value(timing.cads)}```",
                inline=False,
            )

        return embed


class GenerationSelectionView(discord.ui.View):
    """View für Generation-Auswahl"""

    def __init__(self, generations: List[str], bot):
        super().__init__(timeout=180)
        self.add_item(GenerationSelect(generations, bot))


class PresetSelectionView(discord.ui.View):
    """View für Preset-Auswahl"""

    def __init__(self, presets: List[Dict[str, Any]], generation: str):
        super().__init__(timeout=180)
        self.add_item(PresetSelect(presets, generation))


class Timings(commands.Cog):
    """Cog für Memory-Timing-Suche und -Anzeige mit Dropdown-Interface"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="timings",
        description="Durchsuche Memory-Timing-Datenbank mit Dropdown-Interface",
    )
    @track_command_usage
    async def timings(self, ctx: commands.Context):
        """Zeige Memory-Timing-Interface mit Dropdown-Auswahl"""

        await ctx.defer()

        try:
            # Hole verfügbare Generationen
            options = await self.bot.db.get_memory_timing_filter_options()
            generations = options.get("generations", [])

            if not generations:
                embed = EmbedFactory.error_embed(
                    "Keine Daten verfügbar",
                    "Es sind keine Timing-Daten in der Datenbank verfügbar.",
                )
                await ctx.send(embed=embed)
                return

            # Erstelle Generation-Auswahl-View
            view = GenerationSelectionView(generations, self.bot)
            embed = discord.Embed(
                title="Memory Timings",
                description="Wähle zuerst eine **CPU-Generation** aus:",
                color=discord.Color.blurple(),
            )

            await ctx.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Timings-Interface: {e}")
            embed = EmbedFactory.error_embed(
                "Datenbankfehler", "Fehler beim Laden der Timing-Daten."
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Setup-Funktion für die Cog"""
    await bot.add_cog(Timings(bot))
