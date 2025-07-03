from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

from excel_reader import read_excel_with_required_columns
from logger import logger, BASE_DIR

class ExcelFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".xlsx"):
            logger.info(f"New file detected: {event.src_path} & processing will be started in 2 seconds.")
            time.sleep(2)  # Wait to ensure file is fully written
            logger.info(f"Processing file: {event.src_path}")
            process_excel_file(event.src_path)

def process_excel_file(file_path):
    # Your logic to read and process the Excel file
    data=read_excel_with_required_columns(file_path)
    print(data)
    

if __name__ == "__main__":
    event_handler = ExcelFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(BASE_DIR / "input"), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
