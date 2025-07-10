import os
import time
import shutil
import logging
import warnings
import urllib3
logging.getLogger("urllib3.connectionpool").propagate = False
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)
logging.getLogger("selenium").setLevel(logging.CRITICAL)
logging.getLogger("websockets").setLevel(logging.CRITICAL)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
from watchdog.observers import Observer
from pathlib import Path
from logger import logger
from config import INPUT_DIR, PROCESSED_DIR, OUTPUT_DIR, GLASSBOX_URL, MAX_WORKERS
from glassbox_scraper import create_silent_edge_driver, wait_for_authentication, process_glassbox_links
from excel_reader import read_excel_with_required_columns
from file_operations import initialize_output_excel
from cert_updater import update_certifi
from utils import wait_until_file_is_ready
from shared import ExcelHandler, executor

# Suppress noisy logs from urllib3, selenium, and websockets
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)


def handle_existing_files(driver):
    logger.info("Scanning for existing Excel files in input directory...")
    for file_name in os.listdir(INPUT_DIR):
        if file_name.endswith(".xlsx"):
            file_path = Path(INPUT_DIR) / file_name
            logger.info(f"Found existing file: {file_path}, submitting for processing.")
            handler = ExcelHandler(driver)
            executor.submit(handler.safe_process_file, str(file_path))


def main():
    logger.info(" Starting SageWatch service")

    # Setup certificates for LLM
    logger.info("Setting up certificates for GenAI API...")
    if update_certifi():
        logger.info("Certificate setup completed")
    else:
        logger.warning("Certificate setup failed - LLM may not work")

    # Start browser and authenticate
    logger.info(" Launching browser...")
    driver = create_silent_edge_driver()
    driver.get(GLASSBOX_URL)
    wait_for_authentication(driver)
    logger.info(" Authentication successful")

    # Handle existing files
    logger.info("Checking for existing files in input directory...")
    executor.submit(handle_existing_files, driver)

    # Start folder watcher
    event_handler = ExcelHandler(driver)
    observer = Observer()
    observer.schedule(event_handler, path=str(INPUT_DIR), recursive=False)
    observer.start()
    logger.info(f" Watching folder: {INPUT_DIR}")

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info(" Stopping service due to KeyboardInterrupt...")
        observer.stop()
        driver.quit()
        executor.shutdown(wait=True)
    observer.join()
    logger.info(" Service stopped")


if __name__ == "__main__":
    main()
