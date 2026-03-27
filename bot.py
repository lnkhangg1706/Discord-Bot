import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
from collections import deque
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '!'

if not TOKEN:
    print("⭕ Lỗi: Chưa tìm thấy Token. Hãy kiểm tra file .env")
    exit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True)

queues = {}

ytdl_format_options = {
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

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration_string', 'Unknown')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(
                None, 
                lambda: ytdl.extract_info(url, download=not stream)
            )
            
            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except Exception as e:
            print(f"Lỗi tải nhạc: {e}")
            raise

def check_queue(ctx, guild_id):
    if guild_id in queues and queues[guild_id]:
        song_data = queues[guild_id].popleft()
        asyncio.run_coroutine_threadsafe(play_song(ctx, song_data), bot.loop)

async def play_song(ctx, song_data):
    try:
        if not ctx.voice_client:
            return
            
        source_url = song_data.get('webpage_url', song_data['url'])
        player = await YTDLSource.from_url(source_url, loop=bot.loop, stream=True)
        
        def after_playing(error):
            if error:
                print(f"Lỗi player: {error}")
            check_queue(ctx, ctx.guild.id)
        
        ctx.voice_client.play(player, after=after_playing)
        
        requester = f"<@{song_data.get('requester_id')}>" if song_data.get('requester_id') else song_data.get('requester_name', 'Unknown')
        
        embed = discord.Embed(
            title="🎶 Đang phát nhạc", 
            description=f"**[{player.title}]({player.webpage_url or source_url})**", 
            color=discord.Color.green()
        )
        
        if player.thumbnail: 
            embed.set_thumbnail(url=player.thumbnail)
            
        embed.add_field(name="⏱ Thời lượng", value=player.duration, inline=True)
        embed.add_field(name="👤 Yêu cầu bởi", value=requester, inline=True)
        embed.set_footer(text="Bot by Khang")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        song_title = song_data.get('title', 'Unknown')
        print(f"⭕ Không thể phát bài: {song_title}")
        print(f"   Lỗi chi tiết: {e}")
        await ctx.send(f"⭕ Không thể phát bài **{song_title}**. Đang chuyển sang bài tiếp theo...")
        check_queue(ctx, ctx.guild.id)

@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name="hay cho con chiu kho thay em"
        )
    )

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client and len(voice_client.channel.members) == 1:
        await asyncio.sleep(60)
        if voice_client.is_connected() and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            if member.guild.id in queues:
                queues[member.guild.id].clear()

@bot.command(name='join', aliases=['j'])
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("⭕ Bạn cần vào kênh voice trước!")
    
    channel = ctx.author.voice.channel
    
    if ctx.voice_client is None:
        await channel.connect()
        await ctx.send(f"✅ Đã tham gia **{channel.name}**")
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)
        await ctx.send(f"✅ Đã chuyển sang **{channel.name}**")

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("⭕ Bạn chưa vào voice!")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        try:
            if not query.startswith("http"):
                query = f"ytsearch:{query}"

            info = await bot.loop.run_in_executor(
                None, 
                lambda: ytdl.extract_info(query, download=False)
            )
            
            if not info:
                return await ctx.send("⭕ Không tìm thấy nhạc.")
            
            songs_to_add = []
            req_id = ctx.author.id
            req_name = ctx.author.name

            if 'entries' in info:
                if not info['entries']:
                    return await ctx.send("⭕ Không tìm thấy kết quả.")
                entry = info['entries'][0]
            else:
                entry = info

            song_data = {
                'url': entry['url'], 
                'webpage_url': entry.get('webpage_url', entry.get('url')),
                'title': entry.get('title', 'Unknown'),
                'requester_id': req_id,
                'requester_name': req_name
            }
            
            if ctx.guild.id not in queues:
                queues[ctx.guild.id] = deque()
            
            queues[ctx.guild.id].append(song_data)
            
            if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                song_data = queues[ctx.guild.id].popleft()
                await play_song(ctx, song_data)
            else:
                embed = discord.Embed(
                    title="➕ Đã thêm vào hàng chờ",
                    description=f"**{song_data['title']}**\nVị trí: `{len(queues[ctx.guild.id])}`",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send("⭕ Không tìm thấy nhạc hoặc có lỗi xảy ra.")
            print(f"Lỗi play: {e}")

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ **Đã tạm dừng nhạc.**")
    else:
        await ctx.send("⭕ Không có nhạc đang phát.")

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ **Tiếp tục phát nhạc.**")
    else:
        await ctx.send("⭕ Nhạc đang không bị tạm dừng.")

@bot.command(name='skip', aliases=['next', 's'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ **Đã chuyển bài!**")
    else:
        await ctx.send("⭕ Không có nhạc đang phát.")

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
        ctx.voice_client.stop()
        await ctx.send("⏹ **Đã dừng và xóa hàng chờ.**")
    else:
        await ctx.send("⭕ Bot không trong voice channel.")

@bot.command(name='queue', aliases=['q'])
async def queue_cmd(ctx):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        return await ctx.send("📭 Hàng chờ trống.")
    
    q = list(queues[ctx.guild.id])
    embed = discord.Embed(
        title=f"📜 Hàng chờ ({len(q)} bài)", 
        color=discord.Color.teal()
    )
    
    desc = ""
    for i, s in enumerate(q[:10], 1):
        title = s['title'][:50] + "..." if len(s['title']) > 50 else s['title']
        desc += f"`{i}.` **[{title}]({s['webpage_url']})**\n"
    
    if len(q) > 10:
        desc += f"\n*...và còn {len(q)-10} bài khác*"
    
    embed.description = desc
    await ctx.send(embed=embed)

@bot.command(name='remove', aliases=['rm'])
async def remove(ctx, index: int):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        return await ctx.send("⭕ Hàng chờ trống.")
    
    if 1 <= index <= len(queues[ctx.guild.id]):
        removed = list(queues[ctx.guild.id])[index - 1]
        del queues[ctx.guild.id][index - 1]
        await ctx.send(f"🗑 Đã xóa: **{removed['title']}**")
    else:
        await ctx.send(f"⭕ Số không hợp lệ. Hàng chờ có {len(queues[ctx.guild.id])} bài.")

@bot.command(name='clear')
async def clear(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        count = len(queues[ctx.guild.id])
        queues[ctx.guild.id].clear()
        await ctx.send(f"🗑 Đã xóa **{count}** bài khỏi hàng chờ.")
    else:
        await ctx.send("⭕ Hàng chờ đã trống.")

@bot.command(name='quit', aliases=['leave', 'dc'])
async def quit_cmd(ctx):
    if ctx.voice_client:
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋 **Đã thoát voice channel.**")
    else:
        await ctx.send("⭕ Bot không trong voice channel.")

@bot.command(name='help', aliases=['h'])
async def help_cmd(ctx):
    embed = discord.Embed(
        title="BẢNG ĐIỀU KHIỂN", 
        color=discord.Color.gold()
    )
    embed.add_field(
        name="Âm nhạc",
        value=(
            "`!play <tên/link>` - Phát nhạc\n"
            "`!pause` - Tạm dừng\n"
            "`!resume` - Tiếp tục\n"
            "`!skip` - Chuyển bài\n"
            "`!stop` - Dừng hẳn"
        ),
        inline=False
    )
    embed.add_field(
        name="Hàng chờ",
        value=(
            "`!queue` - Xem hàng chờ\n"
            "`!remove <số>` - Xóa bài\n"
            "`!clear` - Xóa tất cả"
        ),
        inline=False
    )
    embed.add_field(
        name="Khác",
        value=(
            "`!join` - Vào voice\n"
            "`!quit` - Thoát voice\n"
            "`!help` - Trợ giúp"
        ),
        inline=False
    )
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    embed.set_footer(text="Bot by Khang")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⭕ Thiếu tham số. Gõ `!help` để xem hướng dẫn.")
    elif isinstance(error, commands.CommandNotFound):
        pass 
    else:
        print(f"Lỗi: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
