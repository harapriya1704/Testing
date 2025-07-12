# ... existing imports ...

def main():
    logger.info(" Starting SageWatch service")
    
    # Certificate setup REMOVED from here
    
    # Start folder watcher without initial authentication
    observer = Observer()
    event_handler = ExcelHandler()
    observer.schedule(event_handler, path=str(INPUT_DIR), recursive=False)
    observer.start()
    logger.info(f" Watching folder: {INPUT_DIR}")

    # Handle existing files
    logger.info("Checking for existing files in input directory...")
    for file_name in os.listdir(INPUT_DIR):
        if file_name.endswith(".xlsx"):
            file_path = Path(INPUT_DIR) / file_name
            logger.info(f"Found existing file: {file_path}")
            executor.submit(event_handler.safe_process_file, str(file_path))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info(" Stopping service...")
        observer.stop()
        executor.shutdown(wait=True)
    observer.join()
    logger.info(" Service stopped")
