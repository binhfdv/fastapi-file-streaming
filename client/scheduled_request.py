import requests
import time
import os
import schedule
from urllib.parse import unquote
from datetime import datetime
import argparse
from logger import CustomLogger

log = CustomLogger()

# Configuration
API_BASE_URL = "http://127.0.0.1:5000/stream"
PROJECT_NAME = "foo"
EXTENSION = "drc"
SAVE_DIR = "./downloads"

# Ensure save directory exists
os.makedirs(SAVE_DIR, exist_ok=True)

def get_filename_from_response(response):
    """Extract filename from Content-Disposition header."""
    content_disp = response.headers.get("Content-Disposition")
    if content_disp and "filename=" in content_disp:
        filename = content_disp.split("filename=")[1].strip().strip('"')
        return unquote(filename)  # Handle URL encoding
    return None  # Fallback to default if no filename is provided

def fetch_zip():
    """Fetch and save ZIP file from API while keeping the original filename."""
    url = f"{API_BASE_URL}/{PROJECT_NAME}/{EXTENSION}"
    
    try:
        response = requests.get(url, stream=True)
        log.error(str(response.raise_for_status()))  # Raise error for bad responses (4xx, 5xx)

        # Get filename from response headers
        filename = get_filename_from_response(response)
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{PROJECT_NAME}_{timestamp}.zip"  # Fallback

        file_path = os.path.join(SAVE_DIR, filename)

        # Save the file
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        log.info(f"[✓] Downloaded: {file_path}")

    except requests.RequestException as e:
        try:
            log.warning(f"[✗] Failed to fetch ZIP: {e.response.text}")

        except Exception as e:
            log.error(e)
            log.debug("... cannot connect to server")

if __name__ == "__main__":
    log.info("Starting periodic fetch...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default="2")
    args = parser.parse_args()

    log.info(f"Request interval is {args.interval} seconds")
    # Schedule periodic fetching
    schedule.every(args.interval).seconds.do(fetch_zip)
    fetch_zip()  # Run once immediately
    while True:
        schedule.run_pending()
        time.sleep(1)

