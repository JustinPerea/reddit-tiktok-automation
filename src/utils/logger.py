"""
Logging configuration for the application.
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from loguru import logger

from config.settings import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """Setup application logging configuration."""
    settings = get_settings()
    
    # Remove default loguru handler
    logger.remove()
    
    # Set log level
    level = log_level or settings.LOG_LEVEL
    
    # Create logs directory
    logs_dir = settings.project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler for general logs
    logger.add(
        logs_dir / "app.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # Error file handler
    logger.add(
        logs_dir / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 week",
        retention="4 weeks",
        compression="zip"
    )
    
    # Video processing logs
    logger.add(
        logs_dir / "video_processing.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: "video" in record["name"].lower() or "processing" in record["message"].lower(),
        rotation="1 day",
        retention="7 days"
    )
    
    # TTS processing logs
    logger.add(
        logs_dir / "tts_processing.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: "tts" in record["name"].lower() or "speech" in record["message"].lower(),
        rotation="1 day",
        retention="7 days"
    )
    
    logger.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)