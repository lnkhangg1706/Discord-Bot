"""
Logging utility for Discord Music Bot.
Provides centralized logging configuration for the application.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import config


def setup_logger(name: str, log_file: Optional[str] = None, level: str = config.LOG_LEVEL) -> logging.Logger:
    """
    Set up and return a logger instance with file and console handlers.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional log file path. If None, uses config.LOG_FILE
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger
    
    # Create formatters
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = config.LOG_FILE
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning(f"⚠️ Cannot write to log file: {log_file}")
    
    return logger


# Create a logger instance for the bot
logger = setup_logger('DiscordBot')
