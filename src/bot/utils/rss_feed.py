"""
RSS Feed Utility Functions für den Loretta Discord Bot
Gemeinsame Funktionen für RSS-Feed Verarbeitung
"""

import asyncio
import logging
import re
from collections.abc import Callable
from typing import Any

import aiohttp
import feedparser

logger = logging.getLogger(__name__)


async def process_rss_feed(
    session: aiohttp.ClientSession | None,
    bot: Any,
    rss_urls: list[str],
    keywords: list[str],
    embed_factory: Callable,
    source_name: str,
    guid_prefix: str,
    search_text_extractor: Callable | None = None,
) -> None:
    """
    Verarbeitet RSS-Feeds und sendet relevante Einträge an konfigurierte Kanäle.

    Args:
        session: aiohttp Client Session
        bot: Discord Bot Instanz
        rss_urls: Liste von RSS-URLs
        keywords: Keywords für Content-Filterung
        embed_factory: Callable zum Erstellen von Discord Embeds
        source_name: Name der Quelle für Logging
        guid_prefix: Präfix für GUID-Generierung
        search_text_extractor: Optional function to extract search text from entry
        feed_sorter: Optional function to sort feed entries
    """
    try:
        if not session:
            logger.error(f"{source_name} - HTTP-Session nicht verfügbar für RSS-Check")
            return

        # News-Kanäle abrufen
        channel_ids = await bot.db.get_news_channels()
        if not channel_ids:
            logger.warning(f"{source_name} - Keine News-Kanäle konfiguriert")
            return

        # Alle Feeds abrufen und kombinieren
        all_entries = []

        for index, rss_url in enumerate(rss_urls):
            feed_type = f"feed_{index}" if len(rss_urls) > 1 else "main"

            try:
                # RSS-Feed abrufen
                async with session.get(rss_url) as response:
                    if response.status != 200:
                        logger.error(
                            f"{source_name} - RSS-Feed Fehler ({feed_type}): HTTP {response.status} für {rss_url}"
                        )
                        continue

                    content = await response.text()

                # RSS-Feed parsen
                feed = feedparser.parse(content)

                if not hasattr(feed, "entries"):
                    logger.error(
                        f"{source_name} RSS-Feed hat ungültiges Format ({feed_type})"
                    )
                    continue

                if not feed.entries:
                    logger.warning(
                        f"{source_name} - Keine Einträge im RSS-Feed ({feed_type}) gefunden: {rss_url}"
                    )
                    continue

                # Entries mit Feed-Typ markieren und zur Liste hinzufügen
                for idx, entry in enumerate(feed.entries):
                    sort_key = idx
                    all_entries.append((entry, feed_type, sort_key))

            except (aiohttp.ClientError, asyncio.TimeoutError):
                logger.error(
                    f"{source_name} - RSS-Feed Verbindungsfehler ({feed_type})"
                )
                continue
            except Exception as e:
                logger.error(
                    f"{source_name} - Fehler beim Abrufen des RSS-Feeds ({feed_type}): {e}"
                )
                continue

        if not all_entries:
            logger.debug(f"{source_name} - Keine Einträge in RSS-Feeds gefunden")
            return

        # Entries sortieren: älteste zuerst (umgekehrt, damit neueste zuletzt gepostet werden)
        all_entries.sort(key=lambda x: x[2], reverse=True)

        # Alle Entries verarbeiten
        new_entries_count = 0
        for entry, feed_type, sort_key in all_entries:
            # GUID für Eindeutigkeit verwenden
            entry_guid = f"{guid_prefix}_{str(getattr(entry, 'id', entry.link))}"
            entry_title = str(entry.title)
            entry_link = str(entry.link)

            # Prüfen, ob bereits gepostet
            if await bot.db.is_rss_entry_posted(entry_guid):
                continue

            # Keywords im Content prüfen
            if search_text_extractor:
                search_text = search_text_extractor(entry)
            else:
                # Standard: Titel und Summary
                search_text = entry_title
                if hasattr(entry, "summary") and entry.summary:
                    search_text += " " + str(entry.summary)

            text_lower = search_text.lower()
            matched_keywords = []

            for keyword in keywords:
                # Verwende Wortgrenzen (\b) für exakte Wort-Übereinstimmung
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    matched_keywords.append(keyword)

            if not matched_keywords:
                # Überspringen ohne zu speichern - nur relevante Einträge werden gespeichert
                continue

            # Embed erstellen
            embed = await embed_factory(entry)

            # An alle konfigurierten Kanäle senden
            for channel_id in channel_ids:
                try:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                        guild_name = (
                            channel.guild.name if channel.guild else "Unknown Guild"
                        )
                        guild_id = (
                            channel.guild.id if channel.guild else "Unknown Guild"
                        )
                        logger.info(
                            f"{source_name} - News gesendet an News-Kanal {channel.name} ({channel_id}) in Guild {guild_name} ({guild_id}): {entry.title}"
                        )
                    else:
                        logger.error(f"Kanal {channel_id} nicht gefunden")
                except Exception as e:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        guild_name = (
                            channel.guild.name if channel.guild else "Unknown Guild"
                        )
                        guild_id = (
                            channel.guild.id if channel.guild else "Unknown Guild"
                        )
                        logger.error(
                            f"Fehler beim Senden von {source_name}-News an Kanal {channel.name} ({channel_id}) in Guild {guild_name} ({guild_id}): {e}"
                        )
                    else:
                        logger.error(
                            f"Fehler beim Senden von {source_name}-News an Kanal {channel_id}: {e}"
                        )

            # Als gepostet markieren
            await bot.db.mark_rss_entry_as_posted(entry_guid, entry_title, entry_link)
            new_entries_count += 1

            # Kleine Pause zwischen den Posts
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Fehler beim {source_name} RSS-Feed Check: {e}")
