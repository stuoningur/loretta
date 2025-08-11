"""
Wetter Befehl für den Loretta Discord Bot
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
from discord.ext import commands

from bot.utils.decorators import track_command_usage
from bot.utils.embeds import EmbedFactory
from bot.utils.responses import defer_response, send_error_response
from utils.logging import log_api_request, log_command_success

logger = logging.getLogger(__name__)


class Weather(commands.Cog):
    """Wetter Befehl für Wetterinformationen und Vorhersagen"""

    def __init__(self, bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self):
        """Initialisiert die HTTP-Session beim Laden des Cogs"""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Schließt die HTTP-Session beim Entladen des Cogs"""
        if self.session:
            await self.session.close()

    def _get_weather_icon_url(self, weather_code: int) -> Optional[str]:
        """Mappt Wetter-Codes zu entsprechenden Icon-URLs aus dem GitHub Repository"""
        weather_icon_mapping = {
            0: "clear@4x.png",  # Klarer Himmel
            1: "mostly-clear@4x.png",  # Überwiegend klar
            2: "partly-cloudy@4x.png",  # Teilweise bewölkt
            3: "overcast@4x.png",  # Bedeckt
            45: "fog@4x.png",  # Nebel
            48: "rime-fog@4x.png",  # Reif Nebel
            51: "light-drizzle@4x.png",  # Leichter Nieselregen
            53: "moderate-drizzle@4x.png",  # Mäßiger Nieselregen
            55: "dense-drizzle@4x.png",  # Starker Nieselregen
            56: "light-freezing-drizzle@4x.png",  # Leichter gefrierender Nieselregen
            57: "dense-freezing-drizzle@4x.png",  # Starker gefrierender Nieselregen
            61: "light-rain@4x.png",  # Leichter Regen
            63: "moderate-rain@4x.png",  # Mäßiger Regen
            65: "heavy-rain@4x.png",  # Starker Regen
            66: "light-freezing-rain@4x.png",  # Leichter gefrierender Regen
            67: "heavy-freezing-rain@4x.png",  # Starker gefrierender Regen
            71: "slight-snowfall@4x.png",  # Leichter Schneefall
            73: "moderate-snowfall@4x.png",  # Mäßiger Schneefall
            75: "heavy-snowfall@4x.png",  # Starker Schneefall
            77: "snowflake@4x.png",  # Schneekörner
            80: "light-rain@4x.png",  # Leichte Regenschauer
            81: "moderate-rain@4x.png",  # Mäßige Regenschauer
            82: "heavy-rain@4x.png",  # Starke Regenschauer
            85: "slight-snowfall@4x.png",  # Leichte Schneeschauer
            86: "heavy-snowfall@4x.png",  # Starke Schneeschauer
            95: "thunderstorm@4x.png",  # Gewitter: Leicht oder mäßig
            96: "thunderstorm-with-hail@4x.png",  # Gewitter mit leichtem Hagel
            99: "thunderstorm-with-hail@4x.png",  # Gewitter mit starkem Hagel
        }
        icon_filename = weather_icon_mapping.get(weather_code, "clear@4x.png")
        return f"https://raw.githubusercontent.com/stuoningur/loretta/master/resources/icons/weather/{icon_filename}"

    def _get_weather_description(self, weather_code: int) -> str:
        """Gibt deutsche Beschreibung für Wetter-Codes zurück"""
        descriptions = {
            0: "Klarer Himmel",
            1: "Überwiegend klar",
            2: "Teilweise bewölkt",
            3: "Bedeckt",
            45: "Nebel",
            48: "Reif Nebel",
            51: "Leichter Nieselregen",
            53: "Mäßiger Nieselregen",
            55: "Starker Nieselregen",
            56: "Leichter gefrierender Nieselregen",
            57: "Starker gefrierender Nieselregen",
            61: "Leichter Regen",
            63: "Mäßiger Regen",
            65: "Starker Regen",
            66: "Leichter gefrierender Regen",
            67: "Starker gefrierender Regen",
            71: "Leichter Schneefall",
            73: "Mäßiger Schneefall",
            75: "Starker Schneefall",
            77: "Schneekörner",
            80: "Leichte Regenschauer",
            81: "Mäßige Regenschauer",
            82: "Starke Regenschauer",
            85: "Leichte Schneeschauer",
            86: "Starke Schneeschauer",
            95: "Gewitter",
            96: "Gewitter mit leichtem Hagel",
            99: "Gewitter mit starkem Hagel",
        }
        return descriptions.get(weather_code, "Unbekannt")

    async def _geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        """Sucht Koordinaten für einen Ortsnamen"""
        try:
            if not self.session:
                logger.error("HTTP-Session nicht initialisiert")
                return None

            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {"name": location, "count": 1, "language": "de", "format": "json"}

            async with self.session.get(url, params=params) as response:
                log_api_request(logger, f"geocoding: {location}", response.status)
                if response.status == 200:
                    data = await response.json()
                    if data and data.get("results"):
                        return data["results"][0]
                return None

        except Exception as e:
            logger.error(f"Fehler beim Geocoding für '{location}': {e}")
            return None

    async def _get_weather_data(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Holt Wetterdaten von der Open-Meteo API"""
        try:
            if not self.session:
                logger.error("HTTP-Session nicht initialisiert")
                return None

            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ],
                "daily": [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                ],
                "timezone": "Europe/Berlin",
                "forecast_days": 7,
            }

            async with self.session.get(url, params=params) as response:
                log_api_request(logger, "weather-data", response.status)
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return data
                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
            return None

    def _format_wind_direction(self, degrees: float) -> str:
        """Konvertiert Windrichtung in Grad zu Himmelsrichtung"""
        directions = [
            "N",
            "NNO",
            "NO",
            "ONO",
            "O",
            "OSO",
            "SO",
            "SSO",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]

    @commands.hybrid_command(
        name="wetter",
        aliases=["w"],
        description="Zeigt aktuelle Wetterdaten und 6-Tage-Vorhersage für einen Ort an",
    )
    @track_command_usage
    async def weather(self, ctx, *, location: str):
        """Zeigt Wetterinformationen für einen angegebenen Ort"""

        # Antwort verzögern für längere Verarbeitung
        if not await defer_response(ctx):
            # Für Präfix-Befehle, Tipp-Indikator senden
            async with ctx.typing():
                pass

        # Ort geokodieren
        geo_data = await self._geocode_location(location)
        if not geo_data:
            await send_error_response(
                ctx,
                "Ort nicht gefunden",
                f"Der Ort '{location}' konnte nicht gefunden werden.",
            )
            return

        # Wetterdaten abrufen
        weather_data = await self._get_weather_data(
            geo_data["latitude"], geo_data["longitude"]
        )
        if not weather_data:
            await send_error_response(
                ctx,
                "Wetterdaten nicht verfügbar",
                "Die Wetterdaten konnten nicht abgerufen werden.",
            )
            return

        # Aktuelles Wetter extrahieren
        current = weather_data["current"]
        daily = weather_data["daily"]

        # Haupt-Embed erstellen
        embed = EmbedFactory.info_command_embed(
            title=f"Wetter für {geo_data['name']}, {geo_data.get('country', '')}",
            description="",
            requester=ctx.author,
        )

        # Aktuelle Wetterinformationen
        current_temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        humidity = current["relative_humidity_2m"]
        weather_code = current["weather_code"]
        wind_speed = current["wind_speed_10m"]
        wind_direction = current["wind_direction_10m"]
        weather_time = current["time"]

        weather_desc = self._get_weather_description(weather_code)
        wind_dir_text = self._format_wind_direction(wind_direction)

        # Wetterdaten-Zeitstempel mit Discord-Formatierung formatieren
        weather_datetime = datetime.fromisoformat(weather_time.replace("Z", "+00:00"))
        weather_timestamp = int(weather_datetime.timestamp())

        current_info = (
            f"**Wetter:** {weather_desc}\n"
            f"**Temperatur:** {str(current_temp).replace('.', ',')}°C (Gefühlt {str(feels_like).replace('.', ',')}°C)\n"
            f"**Luftfeuchtigkeit:** {humidity}%\n"
            f"**Wind:** {str(wind_speed).replace('.', ',')} km/h - {wind_dir_text}\n"
            f"**Datenstand:** <t:{weather_timestamp}:f>"
        )

        embed.add_field(name="Aktuelles Wetter", value=current_info, inline=False)

        # Wetter-Icon als Thumbnail mit Web-URL setzen
        icon_url = self._get_weather_icon_url(weather_code)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # 6-Tage-Vorhersage - 2 Felder pro Zeile
        for i in range(1, 7):  # Heute überspringen, nächste 6 Tage anzeigen
            date = daily["time"][i]
            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            precipitation = daily["precipitation_sum"][i]
            precipitation_prob = daily["precipitation_probability_max"][i]
            forecast_weather_code = daily["weather_code"][i]

            weather_desc = self._get_weather_description(forecast_weather_code)

            # Datum mit deutschen Tagesnamen formatieren
            date_obj = datetime.fromisoformat(date)
            german_days = {
                "Monday": "Montag",
                "Tuesday": "Dienstag",
                "Wednesday": "Mittwoch",
                "Thursday": "Donnerstag",
                "Friday": "Freitag",
                "Saturday": "Samstag",
                "Sunday": "Sonntag",
            }
            english_day = date_obj.strftime("%A")
            day_name = german_days.get(english_day, english_day)
            date_formatted = date_obj.strftime("%d.%m")

            # Vorhersage-Text für diesen Tag erstellen
            forecast_info = (
                f"{weather_desc}\n"
                f"{str(min_temp).replace('.', ',')}° - {str(max_temp).replace('.', ',')}°C\n"
                f"Niederschlag: {precipitation_prob}% ({str(precipitation).replace('.', ',')}mm)"
            )

            embed.add_field(
                name=f"{day_name}, {date_formatted}",
                value=forecast_info,
                inline=True,
            )

            # Unsichtbares Feld nach jedem 2. Vorhersagetag hinzufügen um neue Zeile zu erzwingen (2 Spalten, 3 Zeilen)
            if i % 2 == 0:
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Fußzeile aktualisieren um Datenquelle einzuschließen
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name} • Daten von Open-Meteo",
            icon_url=ctx.author.display_avatar.url,
        )

        # Embed senden (Icon wird als Thumbnail verwendet falls Datei existiert)
        await ctx.send(embed=embed)

        log_command_success(
            logger,
            "wetter",
            ctx.author,
            ctx.guild,
            location=location,
            resolved_location=f"{geo_data['name']}, {geo_data.get('country', '')}",
        )

    @commands.hybrid_command(
        name="weathershort",
        aliases=["ws"],
        description="Zeigt kurze Wetterinformationen für einen Ort an",
    )
    @track_command_usage
    async def weather_short(self, ctx, *, location: str):
        """Zeigt kurze Wetterinformationen für einen angegebenen Ort"""

        # Antwort verzögern für längere Verarbeitung
        if not await defer_response(ctx):
            # Für Präfix-Befehle, Tipp-Indikator senden
            async with ctx.typing():
                pass

        # Ort geokodieren
        geo_data = await self._geocode_location(location)
        if not geo_data:
            await send_error_response(
                ctx,
                "Ort nicht gefunden",
                f"Der Ort '{location}' konnte nicht gefunden werden.",
            )
            return

        # Wetterdaten abrufen
        weather_data = await self._get_weather_data(
            geo_data["latitude"], geo_data["longitude"]
        )
        if not weather_data:
            await send_error_response(
                ctx,
                "Wetterdaten nicht verfügbar",
                "Die Wetterdaten konnten nicht abgerufen werden.",
            )
            return

        # Aktuelles Wetter extrahieren
        current = weather_data["current"]
        current_temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        weather_code = current["weather_code"]
        weather_time = current["time"]

        weather_desc = self._get_weather_description(weather_code)

        # Wetterdaten-Zeitstempel mit Discord-Formatierung formatieren
        weather_datetime = datetime.fromisoformat(weather_time.replace("Z", "+00:00"))
        weather_timestamp = int(weather_datetime.timestamp())

        # Kompaktes Embed erstellen
        embed = EmbedFactory.info_command_embed(
            title=f"{geo_data['name']}, {geo_data.get('country', '')}",
            description=f"**{weather_desc}**\n{str(current_temp).replace('.', ',')}°C (Gefühlt {str(feels_like).replace('.', ',')}°C)\n**Datenstand:** <t:{weather_timestamp}:f>",
            requester=ctx.author,
        )

        # Wetter-Icon als Thumbnail setzen
        icon_url = self._get_weather_icon_url(weather_code)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # Fußzeile mit Datenquelle und Zeitstempel aktualisieren
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name} • Daten von Open-Meteo",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

        log_command_success(
            logger,
            "weathershort",
            ctx.author,
            ctx.guild,
            location=location,
            resolved_location=f"{geo_data['name']}, {geo_data.get('country', '')}",
        )


async def setup(bot):
    """Lädt das Weather Cog"""
    await bot.add_cog(Weather(bot))
    logger.info("Weather Cog geladen")
