
import os
from concurrent.futures import ThreadPoolExecutor
from watchdog.events import FileSystemEventHandler
from config import INPUT_DIR, PROCESSED_DIR, OUTPUT_DIR
from logger import logger
from utils import wait_until_file_is_ready
from excel_reader import read_excel_with_required_columns
from file_operations import initialize_output_excel
from glassbox_scraper import process_glassbox_links

MAX_WORKERS = 5
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

class ExcelHandler(FileSystemEventHandler):
    def __init__(self, driver):
        self.driver = driver

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            logger.info(f"New file detected: {event.src_path}")
            executor.submit(self.safe_process_file, event.src_path)

    def safe_process_file(self, input_path):
        if wait_until_file_is_ready(input_path):
            self.process_file(input_path)
        else:
            logger.warning(f"File {input_path} was not stable within timeout. Skipping.")

    def process_file(self, input_path):
        try:
            filename = os.path.basename(input_path)
            output_path = OUTPUT_DIR / f"enriched_{filename}"
            processed_path = PROCESSED_DIR / filename

            initialize_output_excel(output_path)
            logger.info(f"Created output file: {output_path}")

            data = read_excel_with_required_columns(input_path)
            logger.info(f"Extracted {len(data)} DSAT records from {filename}")

            process_glassbox_links(data, output_path, self.driver)
            logger.info(f"Processed {len(data)} Glassbox sessions")

            os.rename(input_path, processed_path)
            logger.info(f"Moved {filename} to processed folder")
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
