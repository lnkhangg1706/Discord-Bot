"""
Configuration file for Discord Music Bot.
Contains constants and settings used throughout the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
BOT_PREFIX: str = os.getenv('BOT_PREFIX', '!')
BOT_STATUS_MESSAGE: str = 'hay cho con chiu kho thay em'
BOT_STATUS_TYPE: str = 'listening'

# Validation
if not DISCORD_TOKEN:
    raise RuntimeError('❌ Missing DISCORD_TOKEN in .env file!')

# Music Bot Configuration
YTDL_FORMAT_OPTIONS: dict = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}

FFMPEG_OPTIONS: dict = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

# Player Configuration
DEFAULT_VOLUME: float = 0.5
MIN_VOLUME: int = 1
MAX_VOLUME: int = 100
IDLE_TIMEOUT: int = 60  # Disconnect after 60 seconds of inactivity

# Queue Configuration
MAX_QUEUE_DISPLAY: int = 10  # Show 10 tracks in queue embed
LRU_CACHE_SIZE: int = 128  # Cache size for yt-dlp

# Logging Configuration
LOG_LEVEL: str = 'INFO'
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE: str = 'logs/bot.log'

# Command Aliases
COMMAND_ALIASES: dict = {
    'join': ['j'],
    'play': ['p'],
    'resume': ['r'],
    'skip': ['next', 's'],
    'queue': ['q'],
    'nowplaying': ['np'],
    'volume': ['vol'],
    'remove': ['rm'],
    'quit': ['leave', 'dc'],
    'help': ['h'],
}

# Loop Modes
LOOP_MODES: set = {'none', 'song', 'queue'}
DEFAULT_LOOP_MODE: str = 'none'

# UI Configuration (using emojis and formatting)
EMBED_COLORS: dict = {
    'playing': 0x00FF00,      # Green
    'queue': 0x00FFFF,        # Cyan
    'info': 0xFFD700,         # Gold
    'error': 0xFF0000,        # Red
}

BOT_FOOTER: str = 'Bot by Khang'
