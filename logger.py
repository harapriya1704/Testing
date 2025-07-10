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
logger.propagate = False  # Prevent log duplication

# Formatter for logs
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if not logger.handlers:
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
    console_handler.setLevel(logging.INFO)  # Show only INFO+ in console

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

for noisy_logger in ["httpx", "WDM", "selenium", "urllib3"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
