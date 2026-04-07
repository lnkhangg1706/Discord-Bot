"""
Discord Music Bot - Main Entry Point.
Initializes bot, loads extensions, and handles global events.
"""

import asyncio
from typing import Optional

import discord
from discord.ext import commands

import config
from logger import logger


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
    """
    Triggered when bot successfully connects to Discord.
    Updates bot's status and logs connection info.
    """
    logger.info(f'✅ Bot online: {bot.user}')
    
    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=config.BOT_STATUS_MESSAGE,
            )
        )
        logger.info(f'🎵 Status updated to: {config.BOT_STATUS_MESSAGE}')
    except Exception as e:
        logger.error(f'Failed to update presence: {e}')


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    """
    Global error handler for all commands.
    
    Args:
        ctx: Command context
        error: Exception that was raised
    """
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('⭕ Thiếu tham số. Gõ `!help` để xem hướng dẫn.')
        logger.warning(f'Missing argument in {ctx.command}: {error}')
    elif isinstance(error, commands.CommandNotFound):
        logger.debug(f'Command not found: {ctx.message.content}')
        return
    else:
        await ctx.send('⭕ Có lỗi xảy ra. Vui lòng thử lại sau.')
        logger.error(f'Unhandled command error in {ctx.command}: {error}', exc_info=True)


async def load_extensions() -> None:
    """
    Load all bot extensions (cogs) asynchronously.
    Logs success/failure for each extension.
    """
    extensions: list[str] = ['cogs.music']
    
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'✅ Loaded extension: {extension}')
        except Exception as exc:
            logger.error(f'❌ Failed to load extension {extension}: {exc}', exc_info=True)


async def main() -> None:
    """
    Main async entry point for the bot.
    Loads extensions and starts the bot.
    """
    async with bot:
        await load_extensions()
        await bot.start(config.DISCORD_TOKEN)


if __name__ == '__main__':
    logger.info('🚀 Starting Discord Music Bot...')
    asyncio.run(main())
