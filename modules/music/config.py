"""
Music module configuration.
Contains settings specific to music playback and YouTube extraction.
"""

# ── YouTube-DL Options ─────────────────────────────────────────────
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

# ── FFmpeg Options ─────────────────────────────────────────────────
FFMPEG_OPTIONS: dict = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# ── Player Configuration ───────────────────────────────────────────
DEFAULT_VOLUME: float = 0.5
MIN_VOLUME: int = 1
MAX_VOLUME: int = 100
IDLE_TIMEOUT: int = 60        # Giây chờ trước khi tự rời voice nếu không có ai

# ── Queue Configuration ────────────────────────────────────────────
MAX_QUEUE_DISPLAY: int = 10   # Số bài tối đa hiện mỗi trang queue
LRU_CACHE_SIZE: int = 128     # Cache size cho yt-dlp extract_info

# ── Command Aliases ────────────────────────────────────────────────
COMMAND_ALIASES: dict = {
    'join':       ['j'],
    'play':       ['p'],
    'resume':     ['r'],
    'skip':       ['next', 's'],
    'queue':      ['q'],
    'nowplaying': ['np'],
    'volume':     ['vol'],
    'remove':     ['rm'],
    'quit':       ['leave', 'dc'],
    'help':       ['h'],
}

# ── Loop Modes ─────────────────────────────────────────────────────
LOOP_MODES: set = {'none', 'song', 'queue'}
DEFAULT_LOOP_MODE: str = 'none'
