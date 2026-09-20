# -*- coding: utf-8 -*-
"""
Logging setup

print() အစား logging module ကို အသုံးပြုရန် setup လုပ်ပေးသည်။

Features:
    • Console output (stdout)
    • File output (app.log — rotating)
    • Timestamp + level + module name
    • Debug level configurable

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Hello")
    logger.error("Something failed")
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Setup ပြီး/မပြီး flag
_IS_SETUP = False


def setup_logging(
    log_file: str = None,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
) -> None:
    """
    Global logging setup — app တစ်ခုလုံးအတွက် တစ်ကြိမ်သာ ခေါ်ရမည်။

    Args:
        log_file: log file path (None ဖြစ်ပါက console သာ)
        level: logging level (INFO, DEBUG, ...)
        max_bytes: rotating file max size
        backup_count: backup file count
    """
    global _IS_SETUP
    if _IS_SETUP:
        return

    root = logging.getLogger()
    root.setLevel(level)

    # Format
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # File handler (optional)
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(fmt)
            root.addHandler(file_handler)
        except Exception as e:
            print(f"Cannot setup file logging: {e}")

    _IS_SETUP = True


def get_logger(name: str) -> logging.Logger:
    """
    Module-specific logger ရယူသည်။

    Args:
        name: module name (__name__ ကို ပေးပါ)

    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)