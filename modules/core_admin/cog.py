"""
Core Admin Cog - Quản lý các module bot động qua lệnh Discord.
Lệnh: !load, !unload, !reload, !modules, !help (Chỉ dành cho Owner)
"""

import discord
from discord.ext import commands
from core.logger import logger
import core.config as core_config

# Danh sách module có thể dùng cùng mô tả ngắn
AVAILABLE_MODULES: dict[str, str] = {
    'music': 'Module nghe nhạc từ YouTube',
    # Thêm module mới vào đây khi phát triển
    # 'minigame': '🎮 Module minigame trong Discord',
    # 'c2':       '🔧 Module C2 (Command & Control)',
}


class CoreAdmin(commands.Cog):
    """Cog quản trị lõi — luôn hoạt động, không thể tắt."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info('✅ CoreAdmin cog đã khởi động')

    # ── Module Management ──────────────────────────────────────────────

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load_module(self, ctx: commands.Context, module_name: str) -> None:
        """Bật một module. Dùng: !load <tên_module>"""
        try:
            await self.bot.load_extension(f'modules.{module_name}')
            await ctx.send(f'✅ Đã bật module **{module_name}**.')
            logger.info(f'Loaded module: {module_name}')
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f'⭕ Module **{module_name}** đã được bật trước đó.')
        except commands.ExtensionNotFound:
            await ctx.send(f'❌ Không tìm thấy module **{module_name}**. Dùng `!modules` để xem danh sách.')
        except Exception as e:
            await ctx.send(f'❌ Lỗi khi bật module **{module_name}**: {e}')
            logger.error(f'Failed to load module {module_name}: {e}')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload_module(self, ctx: commands.Context, module_name: str) -> None:
        """Tắt một module. Dùng: !unload <tên_module>"""
        if module_name == 'core_admin':
            await ctx.send('⭕ Không thể tắt module quản trị lõi!')
            return
        try:
            await self.bot.unload_extension(f'modules.{module_name}')
            await ctx.send(f'✅ Đã tắt module **{module_name}**.')
            logger.info(f'Unloaded module: {module_name}')
        except commands.ExtensionNotLoaded:
            await ctx.send(f'⭕ Module **{module_name}** chưa được bật.')
        except Exception as e:
            await ctx.send(f'❌ Lỗi khi tắt module **{module_name}**: {e}')
            logger.error(f'Failed to unload module {module_name}: {e}')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_module(self, ctx: commands.Context, module_name: str) -> None:
        """Khởi động lại một module. Dùng: !reload <tên_module>"""
        try:
            await self.bot.reload_extension(f'modules.{module_name}')
            await ctx.send(f'✅ Đã khởi động lại module **{module_name}**.')
            logger.info(f'Reloaded module: {module_name}')
        except commands.ExtensionNotLoaded:
            await ctx.send(f'⭕ Module **{module_name}** chưa được bật. Dùng `!load` trước.')
        except Exception as e:
            await ctx.send(f'❌ Lỗi khi reload module **{module_name}**: {e}')
            logger.error(f'Failed to reload module {module_name}: {e}')

    @commands.command(name='modules', hidden=True)
    @commands.is_owner()
    async def list_modules(self, ctx: commands.Context) -> None:
        """Xem trạng thái tất cả các module."""
        loaded = [
            ext.replace('modules.', '')
            for ext in self.bot.extensions
            if ext.startswith('modules.')
        ]

        embed = discord.Embed(
            title='Quản lý Module',
            description='Trạng thái các module hiện tại:',
            color=core_config.EMBED_COLORS['info'],
        )

        lines = []
        for mod, desc in AVAILABLE_MODULES.items():
            status = '🟢 Đang bật' if mod in loaded else '🔴 Đang tắt'
            lines.append(f'**{mod}** — {desc}\n└ {status}')

        embed.add_field(name='Danh sách Module', value='\n\n'.join(lines) or 'Chưa có module nào.', inline=False)
        embed.add_field(
            name='Lệnh điều khiển',
            value=(
                f'`{core_config.BOT_PREFIX}load <tên>` — Bật module\n'
                f'`{core_config.BOT_PREFIX}unload <tên>` — Tắt module\n'
                f'`{core_config.BOT_PREFIX}reload <tên>` — Khởi động lại module'
            ),
            inline=False,
        )
        embed.set_footer(text=core_config.BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name='adminhelp', hidden=True)
    @commands.is_owner()
    async def admin_help(self, ctx: commands.Context) -> None:
        """Xem hướng dẫn đầy đủ cho Admin."""
        p = core_config.BOT_PREFIX
        embed = discord.Embed(
            title='Hướng dẫn Admin',
            color=core_config.EMBED_COLORS['info'],
        )
        embed.add_field(
            name='Quản lý Module',
            value=(
                f'`{p}modules` — Xem trạng thái tất cả module\n'
                f'`{p}load <tên>` — Bật một module\n'
                f'`{p}unload <tên>` — Tắt một module\n'
                f'`{p}reload <tên>` — Reload module (áp dụng code mới ngay)\n'
            ),
            inline=False,
        )
        embed.add_field(
            name='Ví dụ',
            value=(
                f'`{p}load music` — Bật tính năng nghe nhạc\n'
                f'`{p}unload music` — Tắt tính năng nghe nhạc\n'
                f'`{p}reload music` — Reload module nhạc sau khi sửa code'
            ),
            inline=False,
        )
        embed.add_field(
            name='Khởi động với module sẵn',
            value='```python main.py --modules music```',
            inline=False,
        )
        embed.set_footer(text=core_config.BOT_FOOTER)
        await ctx.send(embed=embed)
