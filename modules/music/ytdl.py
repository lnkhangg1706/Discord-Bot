"""
YouTube DL Source - Xử lý trích xuất audio từ YouTube và stream qua FFmpeg.
"""

import asyncio
from typing import Any, Dict, Optional

import discord
import yt_dlp

from core.logger import logger
import modules.music.config as music_config


# Khởi tạo yt-dlp instance dùng chung
ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(music_config.YTDL_FORMAT_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    """Audio source cho Discord voice, hỗ trợ stream từ YouTube với điều chỉnh âm lượng."""

    def __init__(
        self,
        source: discord.AudioSource,
        *,
        data: Dict[str, Any],
        volume: float = music_config.DEFAULT_VOLUME,
    ) -> None:
        super().__init__(source, volume)
        self.data = data
        self.title: str = data.get('title', 'Unknown')
        self.url: str = data.get('url', '')
        self.duration: str = data.get('duration_string', 'Unknown')
        self.thumbnail: Optional[str] = data.get('thumbnail')
        self.webpage_url: str = data.get('webpage_url', data.get('url', ''))

    @classmethod
    async def from_url(
        cls,
        url: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        stream: bool = True,
    ) -> 'YTDLSource':
        """Tạo YTDLSource từ URL hoặc từ khóa tìm kiếm YouTube."""
        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(url, download=not stream),
        )

        if not data:
            raise ValueError(f'Không thể trích xuất thông tin từ: {url}')

        if 'entries' in data:
            data = data['entries'][0]

        filename: str = data['url'] if stream else ytdl.prepare_filename(data)
        logger.debug(f'Audio source: {data.get("title", "Unknown")}')

        return cls(
            discord.FFmpegPCMAudio(filename, **music_config.FFMPEG_OPTIONS),
            data=data,
        )
