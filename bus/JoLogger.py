import logging
import os
from logging.handlers import RotatingFileHandler

# ── Config ──────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
MAX_BYTES = 2 * 1024 * 1024   # 2 MB per file
BACKUP_COUNT = 4               # 4 backups + 1 active = 5 files = 10 MB max
LOG_FILE = "brain.log"

# ── Format ──────────────────────────────────────────────────────────
FMT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger with rotating file + console output.
    Usage: log = get_logger("SessionManager")
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers twice if get_logger called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(FMT, datefmt=DATE_FMT)

    # ── Console handler (INFO+) ─────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ── Rotating file handler (DEBUG+) ──────────────────────────────
    os.makedirs(LOG_DIR, exist_ok=True)
    file_path = os.path.join(LOG_DIR, LOG_FILE)
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
