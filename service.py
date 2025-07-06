import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger import logger  # Use your custom logger
from config import INPUT_DIR, PROCESSED_DIR, OUTPUT_DIR, GLASSBOX_URL
from glassbox_scraper import create_silent_edge_driver, wait_for_authentication, process_glassbox_links
from excel_reader import read_excel_with_required_columns
from file_operations import initialize_output_excel

class ExcelHandler(FileSystemEventHandler):
    def __init__(self, driver):
        self.driver = driver
        self.processing = False

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            logger.info(f"New file detected: {event.src_path}")
            time.sleep(2)  # Ensure file is fully written
            self.process_file(event.src_path)

    def process_file(self, input_path):
        if self.processing:
            logger.warning("Already processing a file. Skipping...")
            return
            
        self.processing = True
        try:
            filename = input_path.split("\\")[-1]
            output_path = OUTPUT_DIR / f"enriched_{filename}"
            processed_path = PROCESSED_DIR / filename
            
            # Initialize output
            initialize_output_excel(output_path)
            logger.info(f"Created output file: {output_path}")
            
            # Extract data
            data = read_excel_with_required_columns(input_path)
            logger.info(f"Extracted {len(data)} DSAT records from {filename}")
            
            # Process with existing driver
            process_glassbox_links(data, output_path, self.driver)
            logger.info(f"Processed {len(data)} Glassbox sessions")
            
            # Move to processed folder
            shutil.move(input_path, processed_path)
            logger.info(f"Moved {filename} to processed folder")
            
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
        finally:
            self.processing = False

def main():
    logger.info(" Starting SageWatch service")
    
    # Start browser and authenticate
    logger.info(" Launching browser...")
    driver = create_silent_edge_driver()
    driver.get(GLASSBOX_URL)
    wait_for_authentication(driver)
    logger.info(" Authentication successful")
    
    # Start folder watcher
    event_handler = ExcelHandler(driver)
    observer = Observer()
    observer.schedule(event_handler, path=str(INPUT_DIR), recursive=False)
    observer.start()
    logger.info(f" Watching folder: {INPUT_DIR}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info(" Stopping service...")
        observer.stop()
        driver.quit()
    observer.join()
    logger.info(" Service stopped")

if __name__ == "__main__":
    main()
