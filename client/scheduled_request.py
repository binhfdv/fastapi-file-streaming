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

def fetch_zip(api_base_url: str="http://127.0.0.1:5000/stream", project: str="foo", ext: str="drc"):
    """Fetch and save ZIP file from API while keeping the original filename."""
    url = f"{api_base_url}/{project}/{ext}"
    
    try:
        response = requests.get(url, stream=True)
        log.error(str(response.raise_for_status()))  # Raise error for bad responses (4xx, 5xx)

        # Get filename from response headers
        filename = get_filename_from_response(response)
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{project}_{timestamp}.zip"  # Fallback

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
    parser.add_argument("--api", type=str, default="http://127.0.0.1:5000/stream")
    parser.add_argument("--project", type=str, default="foo")
    parser.add_argument("--ext", type=str, default="drc")
    args = parser.parse_args()

    log.info(f"Request interval is {args.interval} seconds")
    # Schedule periodic fetching
    schedule.every(args.interval).seconds.do(lambda: fetch_zip(args.api, args.project, args.ext))
    fetch_zip(args.api, args.project, args.ext)  # Run once immediately
    while True:
        schedule.run_pending()
        time.sleep(1)

