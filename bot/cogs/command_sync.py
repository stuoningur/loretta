"""
Command Synchronisierungs-Befehle für den Loretta Discord Bot
"""

import logging

import discord
from discord.ext import commands

from bot.utils.decorators import track_command_usage

logger = logging.getLogger(__name__)


class CommandSync(commands.Cog):
    """Command Synchronisierungs-Befehle und Funktionen"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="sync", description="Synchronisiert Slash-Commands (nur Bot-Besitzer)"
    )
    @commands.is_owner()
    @track_command_usage
    async def sync_commands(self, ctx, scope: str = "server"):
        """
        Löscht den Command-Tree und synchronisiert die Slash-Commands manuell (nur Bot-Besitzer)

        Args:
            scope: "server" für Serverspezifisch (sofort) oder "global" für global (bis zu 1h)
        """
        try:
            if scope.lower() == "global":
                # Globalen Command-Tree löschen
                self.bot.tree.clear_commands()
                synced = await self.bot.tree.sync()
                embed = discord.Embed(
                    title="Commands synchronisiert",
                    description=f"Command-Tree wurde geleert und {len(synced)} Slash-Commands wurden global synchronisiert! (Kann bis zu 1 Stunde dauern)",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                logger.info(
                    f"Command-Tree geleert und Slash-Commands global synchronisiert von {ctx.author}: {len(synced)} Commands"
                )
            else:
                # Serverspezifische Synchronisation (sofort verfügbar)
                if not ctx.guild:
                    embed = discord.Embed(
                        title="Fehler bei Synchronisation",
                        description="Serverspezifische Synchronisation ist nur auf Servern möglich!",
                        color=discord.Color.red(),
                    )
                    await ctx.send(embed=embed)
                    return

                # Server Command-Tree löschen
                self.bot.tree.clear_commands(guild=ctx.guild)
                # Kopiere globale Commands zu diesem Server für sofortige Verfügbarkeit
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
                embed = discord.Embed(
                    title="Commands synchronisiert",
                    description=f"Command-Tree wurde geleert und {len(synced)} Slash-Commands wurden für diesen Server synchronisiert! (Sofort verfügbar)",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
                logger.info(
                    f"Command-Tree geleert und Slash-Commands für Server {ctx.guild.name} synchronisiert von {ctx.author}: {len(synced)} Commands"
                )

        except Exception as e:
            embed = discord.Embed(
                title="Fehler bei Synchronisation",
                description=f"Fehler beim Synchronisieren: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            logger.error(
                f"Fehler beim manuellen Synchronisieren der Slash-Commands: {e}"
            )


async def setup(bot):
    """Lädt das CommandSync Cog"""
    await bot.add_cog(CommandSync(bot))
    logger.info("CommandSync Cog geladen")
