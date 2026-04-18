# 🎵 Discord Music Bot

Bot Discord modular với kiến trúc Domain-Driven Design, hỗ trợ phát nhạc từ YouTube, quản lý hàng chờ, và tải/gỡ module động qua lệnh Discord.

## Tính năng

- Phát nhạc từ YouTube (tìm kiếm hoặc link trực tiếp)
- Quản lý hàng chờ (queue, shuffle, remove, clear)
- Điều chỉnh âm lượng, chế độ lặp (none/song/queue)
- Auto-disconnect khi không còn ai trong voice
- Hệ thống module động: bật/tắt/reload tính năng qua Discord mà không cần restart
- Logging chuyên nghiệp với UnicodeSafeHandler (hỗ trợ Emoji trên mọi nền tảng)
- Kiến trúc modular, dễ mở rộng thêm tính năng mới

## Yêu cầu

- Python 3.10+
- FFmpeg (cài sẵn trong PATH hoặc đặt cùng thư mục)
- Discord Bot Token ([Tạo tại đây](https://discord.com/developers/applications))

## Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/<username>/discord-bot.git
cd discord-bot
```

### 2. Tạo môi trường ảo và cài dependencies

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

### 3. Cấu hình

Sao chép file mẫu và điền token của bạn:

```bash
cp .env.example .env
```

Mở file `.env` và thay thế giá trị:

```
DISCORD_TOKEN=your_discord_token_here
BOT_PREFIX=!
LOG_LEVEL=INFO
```

### 4. Cài đặt FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Tải từ [ffmpeg.org](https://ffmpeg.org/download.html) và đặt `ffmpeg.exe` vào thư mục dự án
- Hoặc: `choco install ffmpeg` (nếu dùng Chocolatey)

## Chạy Bot

### Chế độ Admin (chỉ lệnh quản trị)
```bash
python main.py
```

### Chạy kèm module nhạc ngay từ đầu
```bash
python main.py --modules music
```

### Chạy nền trên Linux
```bash
nohup python3 main.py --modules music > /dev/null 2>&1 &
```

## Lệnh

### 🎵 Âm nhạc

| Lệnh | Alias | Mô tả |
|-------|-------|-------|
| `!play <tên/link>` | `!p` | Phát nhạc từ YouTube |
| `!pause` | — | Tạm dừng |
| `!resume` | `!r` | Tiếp tục phát |
| `!skip` | `!next`, `!s` | Chuyển bài |
| `!stop` | — | Dừng và xóa hàng chờ |

### 📜 Hàng chờ

| Lệnh | Alias | Mô tả |
|-------|-------|-------|
| `!queue` | `!q` | Xem hàng chờ |
| `!nowplaying` | `!np` | Bài đang phát |
| `!remove <số>` | `!rm` | Xóa bài theo số thứ tự |
| `!clear` | — | Xóa toàn bộ hàng chờ |
| `!shuffle` | — | Xáo trộn hàng chờ |

### ⚙️ Cài đặt

| Lệnh | Alias | Mô tả |
|-------|-------|-------|
| `!volume <1-100>` | `!vol` | Điều chỉnh âm lượng |
| `!loop [none\|song\|queue]` | — | Chế độ lặp |
| `!join` | `!j` | Vào voice channel |
| `!quit` | `!leave`, `!dc` | Rời voice channel |
| `!help` | `!h` | Xem trợ giúp |

### 🔒 Quản trị (Chỉ Owner)

| Lệnh | Mô tả |
|-------|-------|
| `!modules` | Xem trạng thái tất cả module |
| `!load <tên>` | Bật một module |
| `!unload <tên>` | Tắt một module |
| `!reload <tên>` | Reload module (áp dụng code mới ngay) |
| `!adminhelp` | Hướng dẫn đầy đủ cho Admin |

## Cấu trúc dự án

```
discord/
├── main.py                          # Entry point, xử lý CLI args
├── requirements.txt                 # Dependencies
├── .env                             # Secrets (không đưa lên Git)
├── .env.example                     # File mẫu cấu hình
├── .gitignore                       # Danh sách file bị Git bỏ qua
├── README.md                        # Tài liệu dự án
│
├── core/                            # Lõi hệ thống (dùng chung)
│   ├── __init__.py
│   ├── config.py                    # Cấu hình chung (token, prefix, colors)
│   └── logger.py                    # UnicodeSafeHandler — log an toàn mọi nền tảng
│
├── modules/                         # Các module tính năng (tải động)
│   ├── core_admin/                  # Module quản trị (luôn bật)
│   │   ├── __init__.py
│   │   └── cog.py                   # Lệnh: load, unload, reload, modules
│   │
│   └── music/                       # Module nghe nhạc
│       ├── __init__.py
│       ├── cog.py                   # Lệnh: play, pause, skip, queue...
│       ├── config.py                # Cấu hình riêng cho module nhạc
│       └── ytdl.py                  # Xử lý trích xuất audio từ YouTube
│
├── logs/                            # Log files (không đưa lên Git)
└── venv/                            # Môi trường ảo (không đưa lên Git)
```

## Kiến trúc

### Tải Module Động

Bot sử dụng hệ thống Extension của `discord.py` để cho phép bật/tắt tính năng trong lúc bot đang chạy:

```
main.py (Entry Point)
  ├── core/config.py      ← Cấu hình chung
  ├── core/logger.py      ← Logging tập trung
  │
  ├── modules/core_admin/ ← Luôn bật, không thể tắt
  └── modules/music/      ← Tải động qua !load / --modules
```

- **Khởi động:** `python main.py --modules music` hoặc chỉ `python main.py`
- **Runtime:** Dùng `!load music`, `!unload music`, `!reload music` trên Discord

### UnicodeSafeHandler

Giải quyết triệt để lỗi `UnicodeEncodeError` trên Windows Terminal (cp1252):

- Thử ghi log bình thường trước
- Nếu lỗi encoding, ghi trực tiếp bytes UTF-8 xuống `sys.stderr.buffer`
- Không bao giờ crash bot vì lỗi hiển thị log

## Mở rộng

Để thêm module mới (ví dụ: `minigame`):

1. Tạo thư mục `modules/minigame/`
2. Tạo các file:
   - `__init__.py` — export hàm `setup(bot)`
   - `cog.py` — class kế thừa `commands.Cog`
   - `config.py` — cấu hình riêng (nếu cần)
3. Đăng ký trong `modules/core_admin/cog.py` → `AVAILABLE_MODULES`
4. Bật bằng `!load minigame` hoặc `python main.py --modules minigame`

## Bảo mật

- Token được quản lý qua biến môi trường (`.env`), không bao giờ hardcode
- Lệnh quản trị (`load`, `unload`, `reload`) được bảo vệ bởi `@commands.is_owner()`
- File `.env` được liệt kê trong `.gitignore` để tránh lộ khi push lên GitHub
- File `.env.example` chỉ chứa giá trị mẫu, không chứa thông tin thật

## Dependencies

| Package | Mục đích |
|---------|----------|
| `discord.py[voice]` | Framework Discord Bot + hỗ trợ voice |
| `yt-dlp` | Trích xuất audio từ YouTube |
| `python-dotenv` | Đọc biến môi trường từ file `.env` |
| `PyNaCl` | Mã hóa voice (yêu cầu bởi discord.py) |

---

**Made with ❤️ by Khang**
