"""
HWBOT Cog für Loretta Bot
Enthält Kommandos für HWBOT Competition Informationen
"""

import logging

from discord.ext import commands

from bot.utils.decorators import track_command_usage
from bot.utils.embeds import EmbedFactory
from utils.logging import log_command_success

logger = logging.getLogger(__name__)


class HwbotCog(commands.Cog):
    """Cog für HWBOT Competition Informationen"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="hwbot",
        aliases=["rrocc"],
        description="HWBOT Team CUP 2023 Informationen",
    )
    @track_command_usage
    async def hwbot_info(self, ctx: commands.Context) -> None:
        """Zeigt HWBOT Team CUP 2023 Informationen"""
        embed = EmbedFactory.info_command_embed(
            title="HWBOT Team CUP 2023",
            requester=ctx.author,
            description="""[**rules**](https://hwbot.org/benchmarkRules)

[**AMD CPU**](https://hwbot.org/competition/TC2023AMD/)
Stage 1 - PiFast - Opterons only - DDR1
Stage 2 - GPUPI for CPU - 100M - Agena Cores - DDR2
Stage 3 - 7-Zip - AM3+ - DDR3
[*Stage 4 - Geekbench6 - Multi Core - AM4 - DDR4*](https://hwbot.org/competition/TC2023AMD/stage/5688_geekbench6_-_multi_core_-_am4_-_ddr4)
- Use 4 processor core(s) in total.
- Only use processors using socket AM4.
- A verification screenshot is required, using the official background, GB score, CPU-Z 2.06 tabs for CPU, motherboard and memory
[*Stage 5 - y-cruncher - Pi-2.5b - DDR5*](https://hwbot.org/competition/TC2023AMD/stage/5689_y-cruncher_-_pi-2.5b__-_ddr5)
- Processor speed is limited to 5005 MHz.
- Only use processors using socket AM5.

[**INTEL CPU**](https://hwbot.org/competition/TC2023INTEL/)
Stage 1 - CPU Frequency - Celeron S478 - DDR
Stage 2 - SuperPi - 8M - P4 Prescott 1M - DDR2
Stage 3 - 3DMark11 Physics - Core I5 Sandy Bridge - DDR3
[*Stage 4 - HWBOT x265 Benchmark - 1080p - 6 cores - DDR4*](https://hwbot.org/competition/TC2023INTEL/stage/5693_hwbot_x265_benchmark_-_1080p_-_6_cores_-_ddr4)
- Use 6 processor core(s) in total.
- Processors with a socket LGA1700 socket are forbidden.
[*Stage 5 - Geekbench6 - Multi Core - DDR5*](https://hwbot.org/competition/TC2023INTEL/stage/5694_geekbench6_-_multi_core_-_ddr5)
- Use 2,4,6,8 processor core(s) in total.

[**nVIDIA GPU**](https://hwbot.org/competition/TC2023nVIDIA/)
Stage 1 - 3DMark11 - Extreme - SLi GeForce 600 series
[*Stage 2 - 3DMark Vantage - Performance (GPU) - GeForce 2000 series*](https://hwbot.org/competition/TC2023nVIDIA/stage/5681_3dmark_vantage_-_performance_(gpu)_-_geforce_2000_series)
- Only use videocard from the GeForce 2000 Series family.
- Use 1 videocard core(s) in total.
- Use 6 processor core(s) in total.
Stage 3 - 3DMark03 - GeForce 200 series
Stage 4 - 3DMark2001 SE - Geforce 4 series
Stage 5 - 3DMark - Fire Strike (GPU) - Titan Series

[**AMD GPU**](https://hwbot.org/competition/TC2023AMDGPU/)
Stage 1 - 3DMark - Fire Strike (GPU)
Stage 2 - 3DMark06 - Barts cores Crossfire
[*Stage 3 - 3DMark - Wild Life Extreme - RDNA 1.0*](https://hwbot.org/competition/TC2023AMDGPU/stage/5677_3dmark_-_wild_life_extreme_-_rdna_1.0)
- Only use videocard from the RDNA family.
- Use 1 videocard core(s) in total.
Stage 4 - 3DMark - Cloud Gate (GPU) - HD 3000 series
Stage 5 - 3DMark03 - HD 2000 series

[**iGPU**](https://hwbot.org/competition/TC2023iGPU/)
Stage 1 - 3DMark2001 SE - DDR2 - integrated GPU
Stage 2 - Unigine Heaven - Basic - DDR3 - integrated GPU
[*Stage 3 - 3DMark - Sky Diver (GPU) - DDR4 - integrated GPU*](https://hwbot.org/competition/TC2023iGPU/stage/5672_3dmark_-_sky_diver_(gpu)_-_ddr4_-_integrated_gpu)
- Only use processors using socket LGA1151 v2, LGA1200 socket.
- Integrated GPUs only, no dedicated GPUs
[*Stage 4 - 3DMark Vantage - Performance - DDR5 - integrated GPU*](https://hwbot.org/competition/TC2023iGPU/stage/5673_3dmark_vantage_-_performance__-_ddr5_-_integrated_gpu)
- Only use processors using socket AM5.
- Integrated GPUs only, no dedicated GPUs

[**Memory**](https://hwbot.org/competition/TC2023MEM/)
Stage 1 - Memory Frequency - SDR SDRAM
Stage 2 - PiFast - DDR
Stage 3 - SuperPi - 32M - DDR2
[*Stage 4 - Geekbench3 - Single Core - DDR3*](https://hwbot.org/competition/TC2023MEM/stage/5698_geekbench3_-_single_core_-_ddr3)
[*Stage 5 - y-cruncher - Pi-2.5b with BenchMate - DDR4*](https://hwbot.org/competition/TC2023MEM/stage/5699_y-cruncher_-_pi-2.5b_with_benchmate_-_ddr4)
- Processor speed is limited to 4805 MHz.
- Only use DDR4 SDRAM memory.
[*Stage 6 - PYPrime - 32b with BenchMate - DDR5*](https://hwbot.org/competition/TC2023MEM/stage/5700_pyprime_-_32b_with_benchmate_-_ddr5)
- Only use DDR5 SDRAM memory.
- Only use processors using socket AM5.""",
        )
        await ctx.send(embed=embed)
        log_command_success(logger, "hwbot", ctx.author, ctx.guild)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot"""
    await bot.add_cog(HwbotCog(bot))
    logger.info("HWBOT Cog geladen")
