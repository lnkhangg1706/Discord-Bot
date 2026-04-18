"""
Logging utility for Discord Bot.
Provides centralized logging with full Unicode/emoji support on all platforms.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import core.config as config


class UnicodeSafeHandler(logging.StreamHandler):
    """
    A StreamHandler that guarantees Unicode/emoji output on Windows terminals.

    Strategy:
    1. Try normal write (works on Linux/macOS/Windows Terminal with UTF-8)
    2. On UnicodeEncodeError, write UTF-8 bytes directly to the underlying binary
       buffer (sys.stderr.buffer), bypassing Windows' cp1252 codec entirely.
    3. Last resort: silently drop the log line rather than spamming error tracebacks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Normal path — works when terminal supports UTF-8
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record) + self.terminator
                # Write raw UTF-8 bytes straight to the binary buffer
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr.buffer.write(msg.encode('utf-8', errors='replace'))
                    sys.stderr.buffer.flush()
                else:
                    # Absolute last resort: ASCII with replacement characters
                    safe = msg.encode('ascii', errors='replace').decode('ascii')
                    sys.stderr.write(safe)
                    sys.stderr.flush()
            except Exception:
                pass  # Never crash the bot over a log message


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = config.LOG_LEVEL,
) -> logging.Logger:
    """
    Set up and return a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        log_file: Log file path. Defaults to config.LOG_FILE.
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding duplicate handlers on re-import
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(config.LOG_FORMAT)

    # ── Console handler (Unicode-safe on all platforms) ────────────
    console_handler = UnicodeSafeHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ── File handler ───────────────────────────────────────────────
    if log_file is None:
        log_file = config.LOG_FILE

    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(f'Cannot write to log file: {log_file}')

    return logger


# Module-level logger instance shared across the bot
logger = setup_logger('DiscordBot')
