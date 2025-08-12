"""
Datenbank-Modelle für das Loretta-Projekt.
"""

from dataclasses import dataclass, field


@dataclass
class GuildConfig:
    """Datenklasse für Guild-Konfiguration."""

    guild_id: int
    command_prefix: str = "!"
    log_channel_id: int | None = None
    news_channel_id: int | None = None
    birthday_channel_id: int | None = None
    picture_only_channels: list[int] = field(default_factory=list)


@dataclass
class Birthday:
    """Datenklasse für Benutzer-Geburtstag."""

    id: int | None
    guild_id: int
    user_id: int
    birth_day: int
    birth_month: int


@dataclass
class Specification:
    """Datenklasse für Benutzer-Spezifikationen."""

    id: int | None
    guild_id: int
    user_id: int
    specs_text: str
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class CommandStatistic:
    """Datenklasse für Command-Statistiken."""

    id: int | None
    guild_id: int
    user_id: int
    command_name: str
    cog_name: str | None = None
    executed_at: str | None = None
    success: bool = True
    error_message: str | None = None


@dataclass
class MemoryTiming:
    """Datenklasse für Memory-Timings."""

    id: int | None
    generation: str
    name: str
    rank: str | None = None
    vendor: str | None = None
    ics: str | None = None
    memclk: int | None = None
    fclk: int | None = None
    preset: str | None = None
    pdm: str | None = None
    gdm: str | None = None
    vsoc: str | None = None
    vdimm: str | None = None
    vdd: str | None = None
    vddq: str | None = None
    vddio: str | None = None
    vddg: str | None = None
    cldo_vddp: str | None = None
    vddp: str | None = None
    cads: str | None = None
    procodt: str | None = None
    rtts: str | None = None
    tcl: int | None = None
    trcdrp: int | None = None
    trcdwr: int | None = None
    trcd: int | None = None
    trp: int | None = None
    tras: int | None = None
    trc: int | None = None
    trrds: int | None = None
    trrdl: int | None = None
    tfaw: int | None = None
    twtrs: int | None = None
    twtrl: int | None = None
    twr: int | None = None
    trdrdscl: int | None = None
    twrwrscl: int | None = None
    trefi: int | None = None
    trfc: int | None = None
    tcwl: int | None = None
    trtp: int | None = None
    trdwr: int | None = None
    twrrd: int | None = None
    twrwrsc: int | None = None
    twrwrsd: int | None = None
    twrwrdd: int | None = None
    trdrdsc: int | None = None
    trdrdsd: int | None = None
    trdrddd: int | None = None
    tcke: int | None = None
    created_at: str | None = None
