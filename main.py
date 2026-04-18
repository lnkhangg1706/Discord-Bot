"""
Discord Bot - Main Entry Point.
Initializes bot, parses CLI arguments to load dynamic modules, and handles global events.
"""

import asyncio
import argparse

import discord
from discord.ext import commands

from core import config
from core.logger import logger


# Parse command-line args for modules
parser = argparse.ArgumentParser(description='Run Discord Bot with specific modules.')
parser.add_argument('--modules', nargs='*', default=[], help='List of modules to load on startup.')
args = parser.parse_args()


# Initialize bot intents
intents: discord.Intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot: commands.Bot = commands.Bot(
    command_prefix=config.BOT_PREFIX,
    intents=intents,
    help_command=None,
    case_insensitive=True,
)


@bot.event
async def on_ready() -> None:
    """Triggered when bot successfully connects to Discord."""
    logger.info(f'✅ Bot online: {bot.user}')

    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=config.BOT_STATUS_MESSAGE,
            )
        )
        logger.info(f'🎵 Status: {config.BOT_STATUS_MESSAGE}')
    except Exception as e:
        logger.error(f'Failed to update presence: {e}')


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    """Global error handler for all commands."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'⭕ Thiếu tham số. Gõ `{config.BOT_PREFIX}help` để xem hướng dẫn.')
        logger.warning(f'Missing argument in {ctx.command}: {error}')
    elif isinstance(error, commands.CommandNotFound):
        logger.debug(f'Command not found: {ctx.message.content}')
        return
    elif isinstance(error, commands.NotOwner):
        await ctx.send('⛔ Bạn không có quyền sử dụng lệnh này (Yêu cầu Owner).')
        logger.warning(f'Unauthorized access attempt by {ctx.author}')
    else:
        await ctx.send('⭕ Có lỗi xảy ra. Vui lòng thử lại sau.')
        logger.error(f'Unhandled command error in {ctx.command}: {error}', exc_info=True)


async def load_extensions() -> None:
    """Load all bot extensions based on CLI arguments. core_admin always loads first."""
    extensions: list[str] = ['modules.core_admin']

    for mod in args.modules:
        extensions.append(f'modules.{mod}')

    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'✅ Loaded: {extension}')
        except Exception as exc:
            logger.error(f'❌ Failed to load {extension}: {exc}', exc_info=True)


async def main() -> None:
    """Main async entry point for the bot."""
    async with bot:
        await load_extensions()
        await bot.start(config.DISCORD_TOKEN)


if __name__ == '__main__':
    logger.info('🚀 Khởi động Discord Bot...')
    asyncio.run(main())
