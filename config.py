import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = BASE_DIR / "input"
PROCESSED_DIR = BASE_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"
MAX_WORKERS = 5


GLASSBOX_URL = "https://glassbox.dell.com/webinterface/webui/sessions"
WAIT_TIMES = {
    "PAGE_LOAD": 40,
    "GIA_LOAD": 25,
    "SHORT": 10,
    "COOKIE_EXTRACTION": 20
}


for directory in [INPUT_DIR, PROCESSED_DIR, OUTPUT_DIR]:
    directory.mkdir(exist_ok=True)
