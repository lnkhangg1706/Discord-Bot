"""
Music Cog for Discord Music Bot.
Handles all music-related commands including play, pause, queue management, etc.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import discord
from discord.ext import commands

import config
from logger import logger
from utils.ytdl import YTDLSource, ytdl


@dataclass
class Track:
    """
    Represents a music track with metadata.
    
    Attributes:
        title: Track title
        url: Direct audio URL
        webpage_url: YouTube or source URL
        thumbnail: Album art thumbnail URL
        duration: Track duration as string
        requester_id: Discord user ID who requested it
        requester_name: Discord username who requested it
    """
    title: str
    url: str
    webpage_url: str
    thumbnail: Optional[str]
    duration: str
    requester_id: int
    requester_name: str

    @classmethod
    def from_info(cls, info: Dict, requester_id: int, requester_name: str) -> 'Track':
        """
        Create Track instance from yt-dlp info dictionary.
        
        Args:
            info: Dictionary from yt-dlp.extract_info()
            requester_id: Discord user ID
            requester_name: Discord username
        
        Returns:
            Track instance
        """
        return cls(
            title=info.get('title', 'Unknown'),
            url=info.get('url', ''),
            webpage_url=info.get('webpage_url', info.get('url', '')),
            thumbnail=info.get('thumbnail'),
            duration=info.get('duration_string', 'Unknown'),
            requester_id=requester_id,
            requester_name=requester_name,
        )


class GuildMusicState:
    """
    Manages music state for a single guild (server).
    
    Attributes:
        queue: List of Track objects pending playback
        current: Currently playing Track or None
        loop: Loop mode ('none', 'song', or 'queue')
        volume: Current volume (0.0 to 1.0)
    """
    
    def __init__(self) -> None:
        """Initialize a new guild music state."""
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.loop: str = config.DEFAULT_LOOP_MODE
        self.volume: float = config.DEFAULT_VOLUME


class Music(commands.Cog):
    """
    Cog for music playback and queue management.
    Handles voice channels, audio playback, and user commands.
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        """
        Initialize Music cog.
        
        Args:
            bot: Discord bot instance
        """
        self.bot: commands.Bot = bot
        self.states: Dict[int, GuildMusicState] = {}
        logger.info('✅ Music cog initialized')

    def get_state(self, guild: discord.Guild) -> GuildMusicState:
        """
        Get or create music state for a guild.
        
        Args:
            guild: Discord guild
        
        Returns:
            GuildMusicState for the guild
        """
        return self.states.setdefault(guild.id, GuildMusicState())

    async def _play_next(self, ctx: commands.Context) -> None:
        """
        Play next track in queue based on loop mode.
        Called automatically after track finishes.
        
        Args:
            ctx: Command context
        """
        state = self.get_state(ctx.guild)

        # Stop if nothing in queue
        if not state.queue and not state.current:
            return

        # Handle song loop
        if state.loop == 'song' and state.current:
            await self.play_song(ctx, state.current)
            return

        # Handle queue loop
        if state.loop == 'queue' and state.current:
            state.queue.append(state.current)

        # Play next track or clear current
        if state.queue:
            next_track = state.queue.pop(0)
            await self.play_song(ctx, next_track)
        else:
            state.current = None

    async def play_song(self, ctx: commands.Context, track: Track) -> None:
        """
        Play a track in the voice channel.
        Sends now playing embed to chat.
        
        Args:
            ctx: Command context
            track: Track to play
        """
        voice_client = ctx.guild.voice_client
        if not voice_client:
            logger.warning(f'No voice client in guild {ctx.guild.id}')
            return

        try:
            source_url = track.webpage_url or track.url
            player = await YTDLSource.from_url(source_url, loop=self.bot.loop, stream=True)
            player.volume = self.get_state(ctx.guild).volume

            def after_playing(error: Optional[Exception]) -> None:
                """Callback when track finishes playing."""
                if error:
                    logger.error(f'Playback error: {error}')
                asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop)

            voice_client.play(player, after=after_playing)
            
            state = self.get_state(ctx.guild)
            state.current = track

            # Send now playing embed
            requester_mention = f'<@{track.requester_id}>'
            embed = discord.Embed(
                title='🎶 Đang phát nhạc',
                description=f'**[{track.title}]({track.webpage_url})**',
                color=config.EMBED_COLORS['playing'],
            )
            if track.thumbnail:
                embed.set_thumbnail(url=track.thumbnail)

            embed.add_field(name='⏱ Thời lượng', value=track.duration, inline=True)
            embed.add_field(name='👤 Yêu cầu bởi', value=requester_mention, inline=True)
            embed.add_field(name='🔁 Chế độ lặp', value=state.loop, inline=True)
            embed.set_footer(text=config.BOT_FOOTER)

            await ctx.send(embed=embed)
            logger.info(f'Now playing: {track.title} (requested by {track.requester_name})')
        
        except Exception as e:
            logger.error(f'Error playing track {track.title}: {e}', exc_info=True)
            await ctx.send(f'⭕ Lỗi phát nhạc: {str(e)[:100]}')

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """
        Listener for voice channel changes.
        Disconnects bot if it's alone in channel for 60 seconds.
        
        Args:
            member: Member whose state changed
            before: Previous voice state
            after: New voice state
        """
        voice_client = member.guild.voice_client
        
        # Check if bot is alone in channel
        if voice_client and voice_client.channel and len(voice_client.channel.members) == 1:
            await asyncio.sleep(config.IDLE_TIMEOUT)
            
            # Disconnect if still alone
            if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                self.states.pop(member.guild.id, None)
                await voice_client.disconnect()
                logger.info(f'Disconnected from {voice_client.channel.name} - idle')

    @commands.command(name='join', aliases=config.COMMAND_ALIASES['join'])
    async def join(self, ctx: commands.Context) -> None:
        """
        Bot joins the requester's voice channel.
        
        Args:
            ctx: Command context
        """
        # Validate requester is in voice
        if not ctx.author.voice:
            await ctx.send('⭕ Bạn cần vào kênh voice trước!')
            return

        channel = ctx.author.voice.channel
        
        try:
            # Bot not in any channel
            if ctx.voice_client is None:
                await channel.connect()
                await ctx.send(f'✅ Đã tham gia **{channel.name}**')
                logger.info(f'Joined {channel.name} in {ctx.guild.name}')
            
            # Bot in different channel
            elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f'✅ Đã chuyển sang **{channel.name}**')
                logger.info(f'Moved to {channel.name} in {ctx.guild.name}')
            
            # Already in same channel
            else:
                await ctx.send(f'✅ Bot đã ở trong **{channel.name}**')
        
        except Exception as e:
            await ctx.send(f'⭕ Không thể tham gia voice: {str(e)[:100]}')
            logger.error(f'Error joining voice channel: {e}')

    @commands.command(name='play', aliases=config.COMMAND_ALIASES['play'])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """
        Search YouTube and play/queue a track.
        
        Args:
            ctx: Command context
            query: Search term or YouTube URL
        """
        # Validate requester is in voice
        if not ctx.author.voice:
            await ctx.send('⭕ Bạn chưa vào voice!')
            return

        # Bot auto-join if not already in voice
        if ctx.voice_client is None:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f'⭕ Không thể tham gia voice: {str(e)[:100]}')
                return

        # Validate query
        if not query or len(query) > 255:
            await ctx.send('⭕ Vui lòng nhập tên bài hát hoặc link Youtube hợp lệ.')
            return

        async with ctx.typing():
            try:
                # Prepare search query
                search_query = query if query.startswith('http') else f'ytsearch:{query}'
                
                # Extract info
                info = await self.bot.loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(search_query, download=False),
                )

                if not info:
                    await ctx.send('⭕ Không tìm thấy nhạc.')
                    return

                # Handle playlist entries
                if 'entries' in info:
                    if not info['entries']:
                        await ctx.send('⭕ Không tìm thấy kết quả.')
                        return
                    info = info['entries'][0]

                # Create track
                track = Track.from_info(info, ctx.author.id, ctx.author.name)
                state = self.get_state(ctx.guild)
                state.queue.append(track)

                # Send feedback
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused() or state.current:
                    position = len(state.queue)
                    embed = discord.Embed(
                        title='➕ Đã thêm vào hàng chờ',
                        description=f'**{track.title}**\nVị trí: `{position}`',
                        color=config.EMBED_COLORS['queue'],
                    )
                    await ctx.send(embed=embed)
                    logger.info(f'Queued: {track.title} (position {position})')
                else:
                    # Start playing if nothing playing
                    next_track = state.queue.pop(0)
                    await self.play_song(ctx, next_track)
            
            except Exception as e:
                logger.error(f'Error in play command: {e}', exc_info=True)
                await ctx.send('⭕ Không tìm thấy nhạc hoặc có lỗi xảy ra.')

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context) -> None:
        """Pause current playback."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸ **Đã tạm dừng nhạc.**')
            logger.info(f'Paused in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Không có nhạc đang phát.')

    @commands.command(name='resume', aliases=config.COMMAND_ALIASES['resume'])
    async def resume(self, ctx: commands.Context) -> None:
        """Resume paused playback."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶ **Tiếp tục phát nhạc.**')
            logger.info(f'Resumed in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Nhạc đang không bị tạm dừng.')

    @commands.command(name='skip', aliases=config.COMMAND_ALIASES['skip'])
    async def skip(self, ctx: commands.Context) -> None:
        """Skip to next track in queue."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('⏭ **Đã chuyển bài!**')
            logger.info(f'Skipped in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Không có nhạc đang phát.')

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context) -> None:
        """Stop playback and clear queue."""
        if ctx.voice_client:
            self.states.pop(ctx.guild.id, None)
            ctx.voice_client.stop()
            await ctx.send('⏹ **Đã dừng và xóa hàng chờ.**')
            logger.info(f'Stopped in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Bot không trong voice channel.')

    @commands.command(name='queue', aliases=config.COMMAND_ALIASES['queue'])
    async def queue_cmd(self, ctx: commands.Context) -> None:
        """Display current queue."""
        state = self.get_state(ctx.guild)
        
        if not state.queue:
            await ctx.send('📭 Hàng chờ trống.')
            return

        embed = discord.Embed(
            title=f'📜 Hàng chờ ({len(state.queue)} bài)',
            color=config.EMBED_COLORS['queue'],
        )

        lines: List[str] = []
        for index, entry in enumerate(state.queue[:config.MAX_QUEUE_DISPLAY], 1):
            title = entry.title
            if len(title) > 50:
                title = title[:47] + '...'
            lines.append(f'`{index}.` **[{title}]({entry.webpage_url})**')

        embed.description = '\n'.join(lines)
        
        if len(state.queue) > config.MAX_QUEUE_DISPLAY:
            extra = len(state.queue) - config.MAX_QUEUE_DISPLAY
            embed.description += f'\n\n*...và còn {extra} bài khác*'

        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=config.COMMAND_ALIASES['nowplaying'])
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Display currently playing track."""
        state = self.get_state(ctx.guild)
        
        if not state.current:
            await ctx.send('⭕ Hiện không có bài nào đang phát.')
            return

        track = state.current
        embed = discord.Embed(
            title='🎧 Đang phát',
            description=f'**[{track.title}]({track.webpage_url})**',
            color=config.EMBED_COLORS['playing'],
        )
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        embed.add_field(name='⏱ Thời lượng', value=track.duration, inline=True)
        embed.add_field(name='👤 Yêu cầu bởi', value=f'<@{track.requester_id}>', inline=True)
        embed.add_field(name='🔁 Chế độ lặp', value=state.loop, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=config.COMMAND_ALIASES['volume'])
    async def volume(self, ctx: commands.Context, level: int) -> None:
        """
        Set playback volume.
        
        Args:
            ctx: Command context
            level: Volume level 1-100
        """
        # Validate volume level
        if level < config.MIN_VOLUME or level > config.MAX_VOLUME:
            await ctx.send(f'⭕ Vui lòng nhập giá trị {config.MIN_VOLUME}-{config.MAX_VOLUME}.')
            return

        state = self.get_state(ctx.guild)
        state.volume = level / 100

        # Update current playback if available
        if ctx.voice_client and ctx.voice_client.source and hasattr(ctx.voice_client.source, 'volume'):
            ctx.voice_client.source.volume = state.volume

        await ctx.send(f'🔊 Đã đặt âm lượng thành **{level}%**')
        logger.info(f'Volume set to {level}% in {ctx.guild.name}')

    @commands.command(name='loop')
    async def loop(self, ctx: commands.Context, mode: Optional[str] = None) -> None:
        """
        Set loop mode.
        
        Args:
            ctx: Command context
            mode: 'none', 'song', or 'queue' (None toggles)
        """
        state = self.get_state(ctx.guild)
        
        if mode is None:
            # Toggle between none and queue
            state.loop = 'none' if state.loop != 'none' else 'queue'
        elif mode.lower() in config.LOOP_MODES:
            state.loop = mode.lower()
        else:
            await ctx.send(f'⭕ Chế độ loop không hợp lệ. Dùng: {", ".join(config.LOOP_MODES)}')
            return

        await ctx.send(f'🔁 Chế độ lặp hiện tại: **{state.loop}**')
        logger.info(f'Loop mode set to {state.loop} in {ctx.guild.name}')

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context) -> None:
        """Shuffle the queue."""
        state = self.get_state(ctx.guild)
        
        if not state.queue:
            await ctx.send('⭕ Hàng chờ trống.')
            return

        random.shuffle(state.queue)
        await ctx.send('🔀 Đã xáo trộn hàng chờ.')
        logger.info(f'Shuffled queue in {ctx.guild.name}')

    @commands.command(name='remove', aliases=config.COMMAND_ALIASES['remove'])
    async def remove(self, ctx: commands.Context, index: int) -> None:
        """
        Remove track from queue.
        
        Args:
            ctx: Command context
            index: Queue position (1-based)
        """
        state = self.get_state(ctx.guild)
        
        if not state.queue:
            await ctx.send('⭕ Hàng chờ trống.')
            return

        if 1 <= index <= len(state.queue):
            removed = state.queue.pop(index - 1)
            await ctx.send(f'🗑 Đã xóa: **{removed.title}**')
            logger.info(f'Removed {removed.title} from queue in {ctx.guild.name}')
        else:
            await ctx.send(f'⭕ Số không hợp lệ. Hàng chờ có {len(state.queue)} bài.')

    @commands.command(name='clear')
    async def clear(self, ctx: commands.Context) -> None:
        """Clear entire queue."""
        state = self.get_state(ctx.guild)
        
        if state.queue:
            count = len(state.queue)
            state.queue.clear()
            await ctx.send(f'🗑 Đã xóa **{count}** bài khỏi hàng chờ.')
            logger.info(f'Cleared queue ({count} tracks) in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Hàng chờ đã trống.')

    @commands.command(name='quit', aliases=config.COMMAND_ALIASES['quit'])
    async def quit_cmd(self, ctx: commands.Context) -> None:
        """Disconnect bot from voice channel."""
        if ctx.voice_client:
            channel_name = ctx.voice_client.channel.name
            self.states.pop(ctx.guild.id, None)
            await ctx.voice_client.disconnect()
            await ctx.send('👋 **Đã thoát voice channel.**')
            logger.info(f'Disconnected from {channel_name} in {ctx.guild.name}')
        else:
            await ctx.send('⭕ Bot không trong voice channel.')

    @commands.command(name='help', aliases=config.COMMAND_ALIASES['help'])
    async def help_cmd(self, ctx: commands.Context) -> None:
        """Display help message with all commands."""
        embed = discord.Embed(
            title='BẢNG ĐIỀU KHIỂN',
            color=config.EMBED_COLORS['info'],
        )
        embed.add_field(
            name='🎵 Âm nhạc',
            value=(
                f'`{config.BOT_PREFIX}play <tên/link>` - Phát nhạc\n'
                f'`{config.BOT_PREFIX}pause` - Tạm dừng\n'
                f'`{config.BOT_PREFIX}resume` - Tiếp tục\n'
                f'`{config.BOT_PREFIX}skip` - Chuyển bài\n'
                f'`{config.BOT_PREFIX}stop` - Dừng hẳn'
            ),
            inline=False,
        )
        embed.add_field(
            name='📜 Hàng chờ',
            value=(
                f'`{config.BOT_PREFIX}queue` - Xem hàng chờ\n'
                f'`{config.BOT_PREFIX}remove <số>` - Xóa bài\n'
                f'`{config.BOT_PREFIX}clear` - Xóa tất cả\n'
                f'`{config.BOT_PREFIX}shuffle` - Xáo trộn hàng chờ'
            ),
            inline=False,
        )
        embed.add_field(
            name='⚙️ Cài đặt',
            value=(
                f'`{config.BOT_PREFIX}volume <1-100>` - Điều chỉnh âm lượng\n'
                f'`{config.BOT_PREFIX}loop [none|song|queue]` - Chế độ lặp\n'
                f'`{config.BOT_PREFIX}nowplaying` - Bài đang phát'
            ),
            inline=False,
        )
        embed.add_field(
            name='🎤 Khác',
            value=(
                f'`{config.BOT_PREFIX}join` - Vào voice\n'
                f'`{config.BOT_PREFIX}quit` - Thoát voice'
            ),
            inline=False,
        )
        
        if ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        
        embed.set_footer(text=config.BOT_FOOTER)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Load Music cog into bot.
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(Music(bot))
