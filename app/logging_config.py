"""
Centralized logging configuration for the URL Shortener application.

Each logger writes to its own rotating log file with automatic rotation
when files reach 10MB, keeping 5 backup files.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path


# Determine logs directory based on environment
# In Docker: /app/logs, Locally: <project_root>/logs
if os.path.exists("/app"):
    # Running in Docker container
    LOGS_DIR = Path("/app/logs")
else:
    # Running locally - use relative path from this file's location
    # app/logging_config.py -> go up one level to project root, then logs/
    LOGS_DIR = Path(__file__).parent.parent / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Log format with timestamp, logger name, level, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str, log_file: str, level=logging.ERROR) -> logging.Logger:
    """
    Set up a logger with rotating file handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevents duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Creates rotating file handler (10MB max, 5 backups)
    file_handler = RotatingFileHandler(
        filename=LOGS_DIR / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Creates formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Also log to console in development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def configure_logging():
    """
    Configure all application loggers.
    Calling this once at application startup.
    """
    # Set up module-specific loggers
    setup_logger("app.auth", "auth_errors.log")
    setup_logger("app.url", "url_errors.log")
    setup_logger("app.visit", "visit_errors.log")
    setup_logger("app.main", "app.log")
    
    # Set up root logger for catching any unhandled errors in the application
    setup_logger("root", "app.log")
    
    logging.info("Logging system initialized successfully")


# Pre-configured logger instances for easy import
auth_logger = logging.getLogger("app.auth")
url_logger = logging.getLogger("app.url")
visit_logger = logging.getLogger("app.visit")
main_logger = logging.getLogger("app.main")
