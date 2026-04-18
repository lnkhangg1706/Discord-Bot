"""
Core configuration for Discord Bot.
Contains bot-level constants shared across all modules.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env at project root
load_dotenv()

# ── Bot Configuration ─────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
BOT_PREFIX: str = os.getenv('BOT_PREFIX', '!')
BOT_STATUS_MESSAGE: str = 'hay cho con chiu kho thay em'
BOT_STATUS_TYPE: str = 'listening'
BOT_FOOTER: str = 'Bot by Khang'

# Validation
if not DISCORD_TOKEN:
    raise RuntimeError('❌ Missing DISCORD_TOKEN in .env file!')

# ── Logging Configuration ─────────────────────────────────────────
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE: str = 'logs/bot.log'

# ── Embed Colors (shared across all modules) ──────────────────────
EMBED_COLORS: dict = {
    'playing': 0x1DB954,   # Spotify Green
    'queue':   0x5865F2,   # Discord Blurple
    'info':    0xFFD700,   # Gold
    'error':   0xFF4444,   # Soft Red
    'success': 0x57F287,   # Discord Green
}
