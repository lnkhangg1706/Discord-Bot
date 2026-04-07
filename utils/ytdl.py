"""
YouTube DL Source for Discord Music Bot.
Handles audio extraction from YouTube and audio streaming via FFmpeg.
"""

import asyncio
import functools
from typing import Any, Dict, Optional

import discord
import yt_dlp

import config
from logger import logger


# Initialize yt-dlp with config options
ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(config.YTDL_FORMAT_OPTIONS)


@functools.lru_cache(maxsize=config.LRU_CACHE_SIZE)
def extract_info(query: str, download: bool = False) -> Optional[Dict[str, Any]]:
    """
    Extract information from YouTube using yt-dlp with caching.
    
    Args:
        query: Search query or YouTube URL
        download: Whether to download the audio
    
    Returns:
        Dictionary with video information or None if extraction fails
    """
    try:
        return ytdl.extract_info(query, download=download)
    except Exception as e:
        logger.error(f'Error extracting info from {query}: {e}')
        return None


class YTDLSource(discord.PCMVolumeTransformer):
    """
    Audio source for Discord voice using FFmpeg PCM output.
    Handles audio streaming from YouTube videos with volume control.
    """
    
    def __init__(self, source: discord.AudioSource, *, data: Dict[str, Any], volume: float = config.DEFAULT_VOLUME) -> None:
        """
        Initialize YTDL audio source.
        
        Args:
            source: FFmpeg audio source
            data: Video information dictionary
            volume: Volume level (0.0 to 1.0)
        """
        super().__init__(source, volume)
        self.data: Dict[str, Any] = data
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
        stream: bool = True
    ) -> 'YTDLSource':
        """
        Create YTDLSource from a YouTube URL.
        
        Args:
            url: YouTube URL or search query
            loop: Event loop for executor
            stream: Whether to stream (True) or download (False)
        
        Returns:
            YTDLSource instance ready for playback
        
        Raises:
            Exception: If audio extraction or FFmpeg processing fails
        """
        loop = loop or asyncio.get_event_loop()
        
        try:
            # Extract info in executor to avoid blocking
            data = await loop.run_in_executor(
                None,
                lambda: extract_info(url, download=not stream),
            )
            
            if not data:
                raise ValueError(f'Could not extract info from {url}')
            
            # Handle playlist entries
            if 'entries' in data:
                data = data['entries'][0]
            
            # Prepare filename for FFmpeg
            filename: str = data['url'] if stream else ytdl.prepare_filename(data)
            
            logger.debug(f'Created audio source for: {data.get("title", "Unknown")}')
            
            return cls(
                discord.FFmpegPCMAudio(filename, **config.FFMPEG_OPTIONS),
                data=data
            )
        
        except Exception as e:
            logger.error(f'Error creating YTDLSource from {url}: {e}')
            raise
