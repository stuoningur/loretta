"""
Wetter Befehl für den Loretta Discord Bot
"""

import discord
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

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
            0: "clear@4x.png",  # Clear sky
            1: "mostly-clear@4x.png",  # Mainly clear
            2: "partly-cloudy@4x.png",  # Partly cloudy
            3: "overcast@4x.png",  # Overcast
            45: "fog@4x.png",  # Fog
            48: "rime-fog@4x.png",  # Depositing rime fog
            51: "light-drizzle@4x.png",  # Light drizzle
            53: "moderate-drizzle@4x.png",  # Moderate drizzle
            55: "dense-drizzle@4x.png",  # Dense drizzle
            56: "light-freezing-drizzle@4x.png",  # Light freezing drizzle
            57: "dense-freezing-drizzle@4x.png",  # Dense freezing drizzle
            61: "light-rain@4x.png",  # Slight rain
            63: "moderate-rain@4x.png",  # Moderate rain
            65: "heavy-rain@4x.png",  # Heavy rain
            66: "light-freezing-rain@4x.png",  # Light freezing rain
            67: "heavy-freezing-rain@4x.png",  # Heavy freezing rain
            71: "slight-snowfall@4x.png",  # Slight snow fall
            73: "moderate-snowfall@4x.png",  # Moderate snow fall
            75: "heavy-snowfall@4x.png",  # Heavy snow fall
            77: "snowflake@4x.png",  # Snow grains
            80: "light-rain@4x.png",  # Slight rain showers
            81: "moderate-rain@4x.png",  # Moderate rain showers
            82: "heavy-rain@4x.png",  # Violent rain showers
            85: "slight-snowfall@4x.png",  # Slight snow showers
            86: "heavy-snowfall@4x.png",  # Heavy snow showers
            95: "thunderstorm@4x.png",  # Thunderstorm: Slight or moderate
            96: "thunderstorm-with-hail@4x.png",  # Thunderstorm with slight hail
            99: "thunderstorm-with-hail@4x.png",  # Thunderstorm with heavy hail
        }
        icon_filename = weather_icon_mapping.get(weather_code, "clear@4x.png")
        return f"https://raw.githubusercontent.com/stuoningur/loretta/master/data/icons/weather/{icon_filename}"

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
    async def weather(self, ctx, *, location: str):
        """Zeigt Wetterinformationen für einen angegebenen Ort"""

        # Defer response for longer processing (only for slash commands)
        if ctx.interaction:
            await ctx.defer()
        else:
            # For prefix commands, send a typing indicator
            async with ctx.typing():
                pass

        # Geocode the location
        geo_data = await self._geocode_location(location)
        if not geo_data:
            embed = discord.Embed(
                title="Ort nicht gefunden",
                description=f"Der Ort '{location}' konnte nicht gefunden werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)
            return

        # Get weather data
        weather_data = await self._get_weather_data(
            geo_data["latitude"], geo_data["longitude"]
        )
        if not weather_data:
            embed = discord.Embed(
                title="Wetterdaten nicht verfügbar",
                description="Die Wetterdaten konnten nicht abgerufen werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)
            return

        # Extract current weather
        current = weather_data["current"]
        daily = weather_data["daily"]

        # Create main embed
        embed = discord.Embed(
            title=f"Wetter für {geo_data['name']}, {geo_data.get('country', '')}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Current weather info
        current_temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        humidity = current["relative_humidity_2m"]
        weather_code = current["weather_code"]
        wind_speed = current["wind_speed_10m"]
        wind_direction = current["wind_direction_10m"]
        weather_time = current["time"]

        weather_desc = self._get_weather_description(weather_code)
        wind_dir_text = self._format_wind_direction(wind_direction)

        # Format weather data timestamp using Discord formatting
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

        # Set weather icon as thumbnail using web URL
        icon_url = self._get_weather_icon_url(weather_code)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # 6-day forecast - 2 fields per row
        for i in range(1, 7):  # Skip today, show next 6 days
            date = daily["time"][i]
            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            precipitation = daily["precipitation_sum"][i]
            precipitation_prob = daily["precipitation_probability_max"][i]
            forecast_weather_code = daily["weather_code"][i]

            weather_desc = self._get_weather_description(forecast_weather_code)

            # Format date with German day names
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

            # Build forecast text for this day
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

            # Add invisible field after every 2nd forecast day to force new row (2 columns, 3 rows)
            if i % 2 == 0:
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name} • Daten von Open-Meteo",
            icon_url=ctx.author.display_avatar.url,
        )

        # Send embed (icon will be used as thumbnail if file exists)
        await ctx.send(embed=embed)

        logger.info(
            f"Wetter-Befehl ausgeführt von {ctx.author} für '{location}' "
            f"({geo_data['name']}, {geo_data.get('country', '')})"
        )

    @commands.hybrid_command(
        name="weathershort",
        aliases=["ws"],
        description="Zeigt kurze Wetterinformationen für einen Ort an",
    )
    async def weather_short(self, ctx, *, location: str):
        """Zeigt kurze Wetterinformationen für einen angegebenen Ort"""

        # Defer response for longer processing (only for slash commands)
        if ctx.interaction:
            await ctx.defer()
        else:
            # For prefix commands, send a typing indicator
            async with ctx.typing():
                pass

        # Geocode the location
        geo_data = await self._geocode_location(location)
        if not geo_data:
            embed = discord.Embed(
                title="Ort nicht gefunden",
                description=f"Der Ort '{location}' konnte nicht gefunden werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)
            return

        # Get weather data
        weather_data = await self._get_weather_data(
            geo_data["latitude"], geo_data["longitude"]
        )
        if not weather_data:
            embed = discord.Embed(
                title="Wetterdaten nicht verfügbar",
                description="Die Wetterdaten konnten nicht abgerufen werden.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc),
            )
            await ctx.send(embed=embed)
            return

        # Extract current weather
        current = weather_data["current"]
        current_temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        weather_code = current["weather_code"]

        weather_desc = self._get_weather_description(weather_code)

        # Create compact embed
        embed = discord.Embed(
            title=f"{geo_data['name']}, {geo_data.get('country', '')}",
            description=f"**{weather_desc}**\n{str(current_temp).replace('.', ',')}°C (Gefühlt {str(feels_like).replace('.', ',')}°C)",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )

        # Set weather icon as thumbnail
        icon_url = self._get_weather_icon_url(weather_code)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

        logger.info(
            f"Wetter-Kurz-Befehl ausgeführt von {ctx.author} für '{location}' "
            f"({geo_data['name']}, {geo_data.get('country', '')})"
        )


async def setup(bot):
    """Lädt das Weather Cog"""
    await bot.add_cog(Weather(bot))
    logger.info("Weather Cog geladen")
