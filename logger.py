import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Define log directory and file path
BASE_DIR = Path(__file__).resolve().parent
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "SageWatch_logger.log"

# Create a logger
logger = logging.getLogger("SageWatch")
logger.setLevel(logging.DEBUG)

# Formatter for logs
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler with rotation
file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)

# Add handlers to logger
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
