from discord.ext import commands
from .cog import Music

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
