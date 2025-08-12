"""
Picture-Only Channel Monitoring Cog

Dieses Cog überwacht Kanäle, in denen nur Bilder ohne Text erlaubt sind.
Die Verwaltung der Nur-Bild-Kanäle erfolgt über das /config Command.
"""

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from ...main import LorettaBot

logger = logging.getLogger(__name__)


class PictureOnly(commands.Cog):
    """Cog für die Überwachung von Nur-Bild-Kanälen"""

    def __init__(self, bot: "LorettaBot"):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Überwacht Nachrichten in Nur-Bild-Kanälen"""
        # Ignoriere Bot-Nachrichten
        if message.author.bot:
            return

        # Ignoriere DMs
        if not message.guild:
            return

        # Nach diesem Check wissen wir, dass message.channel ein GuildChannel ist
        if not isinstance(message.channel, (discord.TextChannel, discord.Thread)):
            return

        # Prüfe auf Nur-Bild-Kanäle
        try:
            is_picture_only = await self.bot.db.is_picture_only_channel(
                message.guild.id, message.channel.id
            )

            if is_picture_only:
                # Prüfe ob der Autor Admin-Rechte hat
                if (
                    isinstance(message.author, discord.Member)
                    and message.author.guild_permissions.administrator
                ):
                    return  # Admins dürfen alles schreiben

                # Prüfe ob die Nachricht Bilder hat
                has_images = any(
                    attachment.content_type
                    and attachment.content_type.startswith("image/")
                    for attachment in message.attachments
                )

                # Prüfe ob die Nachricht nur Text ohne Bilder ist
                has_only_text = message.content.strip() and not has_images

                # Lösche nur reine Textnachrichten und andere Anhänge (keine Bilder)
                if has_only_text or (message.attachments and not has_images):
                    # Lösche die Nachricht
                    try:
                        await message.delete()

                        # Sende eine ephemere Warnung an den Benutzer
                        embed = discord.Embed(
                            title="Nur Bilder erlaubt",
                            description=f"In {message.channel.mention} sind nur Bilder erlaubt. Bilder mit Text sind erlaubt.\n\nFür Diskussionen bitte die Threads verwenden.",
                            color=discord.Color.red(),
                        )

                        # Versuche eine DM zu senden
                        try:
                            await message.author.send(embed=embed)
                        except discord.Forbidden:
                            # Falls DM fehlschlägt, sende temporäre Nachricht im Kanal
                            try:
                                await message.channel.send(
                                    f"{message.author.mention}",
                                    embed=embed,
                                    delete_after=10,
                                )
                            except (discord.NotFound, discord.Forbidden) as e:
                                logger.warning(
                                    f"Konnte Warnung nicht senden in {message.channel.name}: {e}"
                                )

                        logger.info(
                            f"Nachricht von {message.author.display_name} ({message.author}) in Nur-Bild-Kanal {message.channel.name} gelöscht"
                        )

                    except discord.NotFound:
                        # Nachricht wurde bereits gelöscht, ignoriere
                        logger.debug(
                            f"Nachricht in {message.channel.name} bereits gelöscht"
                        )
                    except discord.Forbidden:
                        logger.warning(
                            f"Keine Berechtigung zum Löschen von Nachrichten in {message.channel.name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Fehler beim Löschen der Nachricht in Nur-Bild-Kanal: {e}"
                        )

        except Exception as e:
            logger.error(f"Fehler bei der Überprüfung des Nur-Bild-Kanals: {e}")


async def setup(bot: "LorettaBot"):
    """Setup-Funktion für das Cog"""
    await bot.add_cog(PictureOnly(bot))
    logger.info("Picture Only Cog geladen")
