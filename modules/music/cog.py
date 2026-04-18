"""
Music Cog - Xử lý phát nhạc, hàng chờ và quản lý voice channel.
Lệnh: play, pause, resume, skip, stop, queue, nowplaying, volume, loop, shuffle, remove, clear, join, quit, help
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import discord
from discord.ext import commands

import core.config as core_config
from core.logger import logger
import modules.music.config as music_config
from .ytdl import YTDLSource


@dataclass
class Track:
    """Đại diện cho một bài nhạc với đầy đủ metadata."""
    title: str
    url: str
    webpage_url: str
    thumbnail: Optional[str]
    duration: str
    requester_id: int
    requester_name: str

    @classmethod
    def from_info(cls, info: Dict, requester_id: int, requester_name: str) -> 'Track':
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
    """Quản lý trạng thái nhạc cho từng server riêng biệt."""
    def __init__(self) -> None:
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.loop: str = music_config.DEFAULT_LOOP_MODE
        self.volume: float = music_config.DEFAULT_VOLUME


class Music(commands.Cog):
    """Cog xử lý toàn bộ chức năng phát nhạc."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.states: Dict[int, GuildMusicState] = {}
        logger.info('✅ Music cog đã khởi động')

    def get_state(self, guild: discord.Guild) -> GuildMusicState:
        """Lấy hoặc tạo mới trạng thái nhạc cho một server."""
        return self.states.setdefault(guild.id, GuildMusicState())

    async def _play_next(self, ctx: commands.Context) -> None:
        """Phát bài tiếp theo trong hàng chờ, xử lý các chế độ lặp."""
        state = self.get_state(ctx.guild)

        if state.loop == 'song' and state.current:
            await self.play_song(ctx, state.current)
            return

        if state.loop == 'queue' and state.current:
            state.queue.append(state.current)

        if state.queue:
            next_track = state.queue.pop(0)
            await self.play_song(ctx, next_track)
        else:
            state.current = None

    async def play_song(self, ctx: commands.Context, track: Track) -> None:
        """Phát một bài nhạc và gửi embed thông tin lên kênh chat."""
        voice_client = ctx.guild.voice_client
        if not voice_client:
            return

        try:
            source_url = track.webpage_url or track.url
            player = await YTDLSource.from_url(source_url, loop=self.bot.loop, stream=True)
            player.volume = self.get_state(ctx.guild).volume

            def after_playing(error: Optional[Exception]) -> None:
                if error:
                    logger.error(f'Lỗi phát nhạc: {error}')
                asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop)

            voice_client.play(player, after=after_playing)

            state = self.get_state(ctx.guild)
            state.current = track

            embed = discord.Embed(
                title='🎶 Đang phát nhạc',
                description=f'**[{track.title}]({track.webpage_url})**',
                color=core_config.EMBED_COLORS['playing'],
            )
            if track.thumbnail:
                embed.set_thumbnail(url=track.thumbnail)
            embed.add_field(name='⏱ Thời lượng', value=track.duration, inline=True)
            embed.add_field(name='👤 Yêu cầu bởi', value=f'<@{track.requester_id}>', inline=True)
            embed.add_field(name='🔁 Chế độ lặp', value=state.loop, inline=True)
            embed.set_footer(text=core_config.BOT_FOOTER)

            await ctx.send(embed=embed)
            logger.info(f'Now playing: {track.title}')

        except Exception as e:
            logger.error(f'Lỗi phát bài {track.title}: {e}')
            await ctx.send(f'⭕ Lỗi phát nhạc: {str(e)[:100]}')

    # ── Voice Events ───────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Tự động thoát voice nếu không còn ai trong kênh."""
        voice_client = member.guild.voice_client
        if voice_client and voice_client.channel and len(voice_client.channel.members) == 1:
            await asyncio.sleep(music_config.IDLE_TIMEOUT)
            if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                self.states.pop(member.guild.id, None)
                await voice_client.disconnect()

    # ── Voice Commands ─────────────────────────────────────────────────

    @commands.command(name='join', aliases=music_config.COMMAND_ALIASES['join'])
    async def join(self, ctx: commands.Context) -> None:
        """Tham gia vào voice channel của bạn."""
        if not ctx.author.voice:
            await ctx.send('⭕ Bạn cần vào kênh voice trước!')
            return
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f'✅ Đã tham gia **{channel.name}**')
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f'✅ Đã chuyển sang **{channel.name}**')
        else:
            await ctx.send(f'✅ Bot đã ở trong **{channel.name}**')

    @commands.command(name='quit', aliases=music_config.COMMAND_ALIASES['quit'])
    async def quit_cmd(self, ctx: commands.Context) -> None:
        """Rời khỏi voice channel."""
        if ctx.voice_client:
            self.states.pop(ctx.guild.id, None)
            await ctx.voice_client.disconnect()
            await ctx.send('👋 **Đã thoát voice channel.**')
        else:
            await ctx.send('⭕ Bot không trong voice channel.')

    # ── Playback Commands ──────────────────────────────────────────────

    @commands.command(name='play', aliases=music_config.COMMAND_ALIASES['play'])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Phát nhạc từ tên bài hoặc link YouTube."""
        if not ctx.author.voice:
            await ctx.send('⭕ Bạn chưa vào voice!')
            return
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                from yt_dlp import YoutubeDL
                search = query if query.startswith('http') else f'ytsearch:{query}'
                with YoutubeDL(music_config.YTDL_FORMAT_OPTIONS) as ydl:
                    info = await self.bot.loop.run_in_executor(
                        None, lambda: ydl.extract_info(search, download=False)
                    )

                if not info:
                    await ctx.send('⭕ Không tìm thấy nhạc.')
                    return
                if 'entries' in info:
                    if not info['entries']:
                        await ctx.send('⭕ Không tìm thấy kết quả.')
                        return
                    info = info['entries'][0]

                track = Track.from_info(info, ctx.author.id, ctx.author.name)
                state = self.get_state(ctx.guild)
                state.queue.append(track)

                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused() or state.current:
                    await ctx.send(f'➕ Đã thêm vào hàng chờ: **{track.title}**')
                else:
                    await self.play_song(ctx, state.queue.pop(0))

            except Exception as e:
                logger.error(f'Lỗi lệnh play: {e}')
                await ctx.send('⭕ Không tìm thấy nhạc hoặc có lỗi xảy ra.')

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context) -> None:
        """Tạm dừng bài đang phát."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸ **Đã tạm dừng nhạc.**')
        else:
            await ctx.send('⭕ Không có nhạc đang phát.')

    @commands.command(name='resume', aliases=music_config.COMMAND_ALIASES['resume'])
    async def resume(self, ctx: commands.Context) -> None:
        """Tiếp tục phát nhạc."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶ **Tiếp tục phát nhạc.**')
        else:
            await ctx.send('⭕ Nhạc đang không bị tạm dừng.')

    @commands.command(name='skip', aliases=music_config.COMMAND_ALIASES['skip'])
    async def skip(self, ctx: commands.Context) -> None:
        """Bỏ qua bài hiện tại."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('⏭ **Đã chuyển bài!**')
        else:
            await ctx.send('⭕ Không có nhạc đang phát.')

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context) -> None:
        """Dừng nhạc và xóa toàn bộ hàng chờ."""
        if ctx.voice_client:
            self.states.pop(ctx.guild.id, None)
            ctx.voice_client.stop()
            await ctx.send('⏹ **Đã dừng và xóa hàng chờ.**')
        else:
            await ctx.send('⭕ Bot không trong voice channel.')

    # ── Queue Commands ─────────────────────────────────────────────────

    @commands.command(name='queue', aliases=music_config.COMMAND_ALIASES['queue'])
    async def queue_cmd(self, ctx: commands.Context) -> None:
        """Xem danh sách hàng chờ."""
        state = self.get_state(ctx.guild)
        if not state.queue:
            await ctx.send('📭 Hàng chờ trống.')
            return

        embed = discord.Embed(
            title=f'📜 Hàng chờ ({len(state.queue)} bài)',
            color=core_config.EMBED_COLORS['queue'],
        )
        lines = []
        for i, entry in enumerate(state.queue[:music_config.MAX_QUEUE_DISPLAY], 1):
            title = entry.title[:50] + '...' if len(entry.title) > 50 else entry.title
            lines.append(f'`{i}.` **[{title}]({entry.webpage_url})**')
        embed.description = '\n'.join(lines)
        if len(state.queue) > music_config.MAX_QUEUE_DISPLAY:
            embed.description += f'\n\n*...và còn {len(state.queue) - music_config.MAX_QUEUE_DISPLAY} bài khác*'
        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=music_config.COMMAND_ALIASES['nowplaying'])
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Xem bài đang phát."""
        state = self.get_state(ctx.guild)
        if not state.current:
            await ctx.send('⭕ Hiện không có bài nào đang phát.')
            return
        track = state.current
        embed = discord.Embed(
            title='🎧 Đang phát',
            description=f'**[{track.title}]({track.webpage_url})**',
            color=core_config.EMBED_COLORS['playing'],
        )
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        embed.add_field(name='⏱ Thời lượng', value=track.duration, inline=True)
        embed.add_field(name='👤 Yêu cầu bởi', value=f'<@{track.requester_id}>', inline=True)
        embed.add_field(name='🔁 Chế độ lặp', value=state.loop, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context) -> None:
        """Xáo trộn hàng chờ ngẫu nhiên."""
        state = self.get_state(ctx.guild)
        if not state.queue:
            await ctx.send('⭕ Hàng chờ trống.')
            return
        random.shuffle(state.queue)
        await ctx.send('🔀 Đã xáo trộn hàng chờ.')

    @commands.command(name='remove', aliases=music_config.COMMAND_ALIASES['remove'])
    async def remove(self, ctx: commands.Context, index: int) -> None:
        """Xóa một bài khỏi hàng chờ theo số thứ tự."""
        state = self.get_state(ctx.guild)
        if not state.queue:
            await ctx.send('⭕ Hàng chờ trống.')
            return
        if 1 <= index <= len(state.queue):
            removed = state.queue.pop(index - 1)
            await ctx.send(f'🗑 Đã xóa: **{removed.title}**')
        else:
            await ctx.send(f'⭕ Số không hợp lệ. Hàng chờ có {len(state.queue)} bài.')

    @commands.command(name='clear')
    async def clear(self, ctx: commands.Context) -> None:
        """Xóa toàn bộ hàng chờ."""
        state = self.get_state(ctx.guild)
        if state.queue:
            count = len(state.queue)
            state.queue.clear()
            await ctx.send(f'🗑 Đã xóa **{count}** bài khỏi hàng chờ.')
        else:
            await ctx.send('⭕ Hàng chờ đã trống.')

    # ── Settings Commands ──────────────────────────────────────────────

    @commands.command(name='volume', aliases=music_config.COMMAND_ALIASES['volume'])
    async def volume(self, ctx: commands.Context, level: int) -> None:
        """Điều chỉnh âm lượng (1-100)."""
        if level < music_config.MIN_VOLUME or level > music_config.MAX_VOLUME:
            await ctx.send(f'⭕ Vui lòng nhập giá trị từ {music_config.MIN_VOLUME} đến {music_config.MAX_VOLUME}.')
            return
        state = self.get_state(ctx.guild)
        state.volume = level / 100
        if ctx.voice_client and ctx.voice_client.source and hasattr(ctx.voice_client.source, 'volume'):
            ctx.voice_client.source.volume = state.volume
        await ctx.send(f'🔊 Đã đặt âm lượng thành **{level}%**')

    @commands.command(name='loop')
    async def loop(self, ctx: commands.Context, mode: Optional[str] = None) -> None:
        """Đặt chế độ lặp: none | song | queue."""
        state = self.get_state(ctx.guild)
        if mode is None:
            state.loop = 'none' if state.loop != 'none' else 'queue'
        elif mode.lower() in music_config.LOOP_MODES:
            state.loop = mode.lower()
        else:
            await ctx.send(f'⭕ Chế độ loop không hợp lệ. Dùng: `none`, `song`, `queue`')
            return
        await ctx.send(f'🔁 Chế độ lặp hiện tại: **{state.loop}**')

    # ── Help Command ───────────────────────────────────────────────────

    @commands.command(name='help', aliases=music_config.COMMAND_ALIASES['help'])
    async def help_cmd(self, ctx: commands.Context) -> None:
        """Hiển thị danh sách lệnh của bot."""
        p = core_config.BOT_PREFIX
        embed = discord.Embed(
            title='BẢNG ĐIỀU KHIỂN',
            color=core_config.EMBED_COLORS['info'],
        )
        embed.add_field(
            name='Âm nhạc',
            value=(
                f'`{p}play <tên/link>` - Phát nhạc\n'
                f'`{p}pause` - Tạm dừng\n'
                f'`{p}resume` - Tiếp tục\n'
                f'`{p}skip` - Chuyển bài\n'
                f'`{p}stop` - Dừng hẳn'
            ),
            inline=False,
        )
        embed.add_field(
            name='Hàng chờ',
            value=(
                f'`{p}queue` - Xem hàng chờ\n'
                f'`{p}remove <số>` - Xóa bài\n'
                f'`{p}clear` - Xóa tất cả\n'
                f'`{p}shuffle` - Xáo trộn hàng chờ'
            ),
            inline=False,
        )
        embed.add_field(
            name='Cài đặt',
            value=(
                f'`{p}volume <1-100>` - Điều chỉnh âm lượng\n'
                f'`{p}loop [none|song|queue]` - Chế độ lặp\n'
                f'`{p}nowplaying` - Bài đang phát'
            ),
            inline=False,
        )
        embed.add_field(
            name='Khác',
            value=(
                f'`{p}join` - Vào voice\n'
                f'`{p}quit` - Thoát voice'
            ),
            inline=False,
        )
        if ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        embed.set_footer(text=core_config.BOT_FOOTER)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Load Music cog vào bot."""
    await bot.add_cog(Music(bot))
