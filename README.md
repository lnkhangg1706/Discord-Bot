# Discord Music Bot

Bot Discord đơn giản với lệnh hát nhạc, vòng chờ và quản lý voice.

## ⚡ Tính năng

- ✅ Phát nhạc từ YouTube
- ✅ Quản lý hàng chờ
- ✅ Điều chỉnh âm lượng
- ✅ Các chế độ lặp (none, song, queue)
- ✅ Auto-disconnect khi bot ở một mình
- ✅ Xáo trộn hàng chờ
- ✅ Logging chi tiết
- ✅ Cấu trúc modular (cogs)

## 📋 Yêu cầu

- Python 3.8+
- FFmpeg
- Discord Bot Token

## 🚀 Cài đặt

### 1. Setup venv và dependencies

```bash
cd /home/bacxiu0duong/projects/discord
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Tạo file `.env`

Tạo file `discord/.env`:

```
DISCORD_TOKEN=your_discord_token_here
BOT_PREFIX=!
```

### 3. Cài đặt FFmpeg (nếu chưa có)

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download từ https://ffmpeg.org/download.html
- Hoặc: `choco install ffmpeg` (nếu dùng Chocolatey)

## 🎮 Chạy bot

```bash
cd /home/bacxiu0duong/projects/discord
source venv/bin/activate
python3 main.py
```

Hoặc chạy ở background:
```bash
nohup python3 main.py > bot.log 2>&1 &
```

Xem logs:
```bash
tail -f bot.log
```

## 📖 Lệnh

### Người dùng Voice

| Lệnh | Alias | Mô tả |
|------|-------|-------|
| `!join` | `!j` | Bot vào voice channel của bạn |
| `!quit` | `!leave`, `!dc` | Bot rời voice channel |

### Người dùng Phát nhạc

| Lệnh | Alias | Mô tả |
|------|-------|-------|
| `!play <tên/link>` | `!p` | Tìm kiếm và phát nhạc từ YouTube |
| `!pause` | - | Tạm dừng nhạc |
| `!resume` | `!r` | Tiếp tục phát nhạc |
| `!skip` | `!next`, `!s` | Chuyển đến bài tiếp theo |
| `!stop` | - | Dừng nhạc và xóa hàng chờ |

### Quản lý Hàng chờ

| Lệnh | Alias | Mô tả |
|------|-------|-------|
| `!queue` | `!q` | Xem hàng chờ (10 bài đầu) |
| `!nowplaying` | `!np` | Hiển thị bài đang phát |
| `!remove <số>` | `!rm` | Xóa bài khỏi hàng chờ |
| `!clear` | - | Xóa toàn bộ hàng chờ |
| `!shuffle` | - | Xáo trộn hàng chờ |

### Cài đặt

| Lệnh | Alias | Mô tả |
|------|-------|-------|
| `!volume <1-100>` | `!vol` | Đặt âm lượng |
| `!loop [none\|song\|queue]` | - | Chế độ lặp nhạc |
| `!help` | `!h` | Hiển thị trợ giúp |

## 📁 Cấu trúc dự án

```
discord/
├── main.py                 # Entry point
├── config.py              # Constants & config
├── logger.py              # Logging setup
├── requirements.txt       # Tất cả dependencies
├── .env                   # Token & prefix (không lưu vào Git)
├── .gitignore            # Ignore patterns
├── README.md             # Documentation
├── logs/                 # Log files
│   └── bot.log
├── cogs/                 # Command modules (cogs)
│   └── music.py         # Music commands
├── utils/               # Utility modules
│   └── ytdl.py          # YouTube DL & audio source
└── venv/                # Virtual environment (không lưu vào Git)
```

## 🛠️ Cấu hình

### file `config.py`

Chỉnh sửa các hằng số ở đây:

- `DISCORD_TOKEN` - Token từ `.env`
- `BOT_PREFIX` - Tiền tố lệnh (mặc định: `!`)
- `YTDL_FORMAT_OPTIONS` - Cấu hình yt-dlp
- `FFMPEG_OPTIONS` - Cấu hình FFmpeg
- `DEFAULT_VOLUME` - Âm lượng mặc định (0.0-1.0)
- `IDLE_TIMEOUT` - Thời gian disconnect nếu bot ở một mình (giây)
- `LOG_LEVEL` - Mức logging (DEBUG, INFO, WARNING, ERROR)

### file `.env`

```
DISCORD_TOKEN=your_token_here
BOT_PREFIX=!
```

## 📊 Logging

Bot sử dụng `logging` module để ghi lại toàn bộ hoạt động:

- **Log file:** `logs/bot.log`
- **Console:** Hiển thị trực tiếp trên terminal

Log bao gồm:
- Bot startup/shutdown
- Lệnh được thực thi
- Lỗi và exceptions
- Hoạt động voice

## 🐛 Xử lý lỗi

Bot xử lý các lỗi sau:

1. **Bot không vào được voice** → Hiển thị lỗi và log
2. **Không tìm thấy bài hát** → Thông báo & retry
3. **Command lỗi** → Global error handler
4. **Timeout voice** → Auto-disconnect

## 🔒 Best Practices

- ✅ **Type hints** - Tất cả functions có type hints
- ✅ **Docstrings** - Mô tả chi tiết cho mỗi class/function
- ✅ **Config centralized** - Tất cả constants trong `config.py`
- ✅ **Logging** - Dùng logging module thay print()
- ✅ **Input validation** - Kiểm tra query, volume input
- ✅ **Error handling** - Try-except phổ biến
- ✅ **Modular code** - Cogs & utils tách biệt
- ✅ **Organized imports** - PEP 8 compliant

## 📝 Lưu ý

- **Không commit `.env`** - Thêm vào `.gitignore`
- **Không commit `venv/`** - Virtual environment
- **Không commit `logs/`** - Optional
- **Không commit `__pycache__/`** - Cache Python

---

**Made with ❤️ by Khang**
