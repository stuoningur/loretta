"""
Command Synchronisierungs-Befehle für den Loretta Discord Bot
"""

from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class CommandSync(commands.Cog):
    """Command Synchronisierungs-Befehle und Funktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx, scope: str = "server"):
        """
        Synchronisiert die Slash-Commands manuell (nur Bot-Besitzer)

        Args:
            scope: "server" für Serverspezifisch (sofort) oder "global" für global (bis zu 1h)
        """
        try:
            if scope.lower() == "global":
                synced = await self.bot.tree.sync()
                await ctx.send(
                    f"✅ {len(synced)} Slash-Commands global synchronisiert! (Kann bis zu 1 Stunde dauern)"
                )
                logger.info(
                    f"Slash-Commands global synchronisiert von {ctx.author}: {len(synced)} Commands"
                )
            else:
                # Serverspezifische Synchronisation (sofort verfügbar)
                if not ctx.guild:
                    await ctx.send(
                        "❌ Serverspezifische Synchronisation nur auf Servern möglich!"
                    )
                    return

                # Kopiere globale Commands zu diesem Server für sofortige Verfügbarkeit
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
                await ctx.send(
                    f"✅ {len(synced)} Slash-Commands für diesen Server synchronisiert! (Sofort verfügbar)"
                )
                logger.info(
                    f"Slash-Commands für Server {ctx.guild.name} synchronisiert von {ctx.author}: {len(synced)} Commands"
                )

        except Exception as e:
            await ctx.send(f"❌ Fehler beim Synchronisieren: {e}")
            logger.error(
                f"Fehler beim manuellen Synchronisieren der Slash-Commands: {e}"
            )


async def setup(bot):
    """Lädt das CommandSync Cog"""
    await bot.add_cog(CommandSync(bot))
    logger.info("CommandSync Cog geladen")
