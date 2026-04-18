from discord.ext import commands
from .cog import CoreAdmin

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoreAdmin(bot))
