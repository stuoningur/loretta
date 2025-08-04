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
        """Mappt Wetter-Codes zu entsprechenden Icon-URLs"""
        weather_icon_mapping = {
            0: "01d",  # Clear sky
            1: "01d",  # Mainly clear
            2: "02d",  # Partly cloudy
            3: "03d",  # Overcast
            45: "50d",  # Fog
            48: "50d",  # Depositing rime fog
            51: "09d",  # Light drizzle
            53: "09d",  # Moderate drizzle
            55: "09d",  # Dense drizzle
            56: "09d",  # Light freezing drizzle
            57: "09d",  # Dense freezing drizzle
            61: "10d",  # Slight rain
            63: "10d",  # Moderate rain
            65: "10d",  # Heavy rain
            66: "10d",  # Light freezing rain
            67: "10d",  # Heavy freezing rain
            71: "13d",  # Slight snow fall
            73: "13d",  # Moderate snow fall
            75: "13d",  # Heavy snow fall
            77: "13d",  # Snow grains
            80: "09d",  # Slight rain showers
            81: "09d",  # Moderate rain showers
            82: "09d",  # Violent rain showers
            85: "13d",  # Slight snow showers
            86: "13d",  # Heavy snow showers
            95: "11d",  # Thunderstorm: Slight or moderate
            96: "11d",  # Thunderstorm with slight hail
            99: "11d",  # Thunderstorm with heavy hail
        }
        icon_code = weather_icon_mapping.get(weather_code, "01d")
        return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

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
                "timezone": "auto",
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
        description="Zeigt aktuelle Wetterdaten und 6-Tage-Vorhersage für einen Ort an",
    )
    async def weather(self, ctx, *, location: str):
        """Zeigt Wetterinformationen für einen angegebenen Ort"""

        # Defer response for longer processing (only for slash commands)
        if hasattr(ctx, "interaction") and ctx.interaction:
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
            if hasattr(ctx, "interaction") and ctx.interaction:
                await ctx.followup.send(embed=embed)
            else:
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
            if hasattr(ctx, "interaction") and ctx.interaction:
                await ctx.followup.send(embed=embed)
            else:
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

        weather_desc = self._get_weather_description(weather_code)
        wind_dir_text = self._format_wind_direction(wind_direction)

        current_info = (
            f"**Wetter:** {weather_desc}\n"
            f"**Temperatur:** {str(current_temp).replace('.', ',')}°C ({str(feels_like).replace('.', ',')}°C)\n"
            f"**Luftfeuchtigkeit:** {humidity}%\n"
            f"**Wind:** {str(wind_speed).replace('.', ',')} km/h - {wind_dir_text}"
        )

        embed.add_field(name="Aktuelles Wetter", value=current_info, inline=False)

        # Set weather icon as thumbnail using web URL
        icon_url = self._get_weather_icon_url(weather_code)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # 6-day forecast - each day as separate field
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
                name=f"{day_name}, {date_formatted}", value=forecast_info, inline=True
            )

        # Footer
        embed.set_footer(
            text=f"Angefordert von {ctx.author.display_name} • Daten von Open-Meteo",
            icon_url=ctx.author.display_avatar.url,
        )

        # Send embed (icon will be used as thumbnail if file exists)
        if hasattr(ctx, "interaction") and ctx.interaction:
            await ctx.followup.send(embed=embed)
        else:
            await ctx.send(embed=embed)

        logger.info(
            f"Wetter-Befehl ausgeführt von {ctx.author} für '{location}' "
            f"({geo_data['name']}, {geo_data.get('country', '')})"
        )


async def setup(bot):
    """Lädt das Weather Cog"""
    await bot.add_cog(Weather(bot))
    logger.info("Weather Cog geladen")
