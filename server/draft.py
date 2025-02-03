from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import os
import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import zipfile
from datetime import datetime
import shutil

# Create a router
router = APIRouter()

class DASHServer():
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, media_path: str = "./media"):
        self.media_path = media_path
        self.config = Config()
        self.config.bind = f"{host}:{port}"
        self.app = FastAPI()
        self.app.include_router(router)
        mimetypes.add_type('application/zip', '.zip')

        self.subscribers = set()  # Store connected clients

    async def watch_folder_and_send_zip(self, project: str, ext: str):
        """Continuously watches for new files and streams ZIP when detected."""
        bar_path = os.path.join(self.media_path, project, "bar")
        os.makedirs(bar_path, exist_ok=True)

        known_files = set(os.listdir(bar_path))  # Track existing files

        while True:
            current_files = set(os.listdir(bar_path))
            new_files = current_files - known_files

            if new_files:
                known_files = current_files  # Update known files

                # Create ZIP and send to clients
                zip_filename, zip_path = self.create_zip_stream(project, ext)
                if zip_filename and self.subscribers:
                    for subscriber in list(self.subscribers):
                        await subscriber.put(zip_path)  # Notify clients with ZIP path

            await asyncio.sleep(2)  # Check every 2 seconds

    def create_zip_stream(self, project: str, ext: str):
        """Create a ZIP file containing all latest files."""
        bar_path = os.path.join(self.media_path, project, "bar")
        bin_path = os.path.join(self.media_path, project, "bin")
        os.makedirs(bin_path, exist_ok=True)

        latest_files = [f for f in os.listdir(bar_path) if f.endswith(ext)]
        if not latest_files:
            return None, None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{ext}_{len(latest_files)}files_{timestamp}.zip"
        zip_path = os.path.join(bar_path, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in latest_files:
                file_path = os.path.join(bar_path, file)
                zipf.write(file_path, arcname=file)

        # Move files to bin after zipping
        for file in latest_files:
            shutil.move(os.path.join(bar_path, file), os.path.join(bin_path, file))

        return zip_filename, zip_path

    def start(self):
        asyncio.run(serve(self.app, self.config))

@router.get("/subscribe/{project}/{ext}")
async def subscribe_for_zip(project: str, ext: str):
    """Client subscribes to automatic ZIP file delivery when new files appear."""
    server = DASHServer()
    queue = asyncio.Queue()
    server.subscribers.add(queue)

    try:
        while True:
            zip_path = await queue.get()  # Wait for ZIP notification

            if os.path.exists(zip_path):
                return StreamingResponse(open(zip_path, "rb"), media_type="application/zip",
                                         headers={"Content-Disposition": f"attachment; filename={os.path.basename(zip_path)}"})
    finally:
        server.subscribers.remove(queue)  # Remove subscriber when done

if __name__ == "__main__":
    server = DASHServer()
    asyncio.create_task(server.watch_folder_and_send_zip("foo", "drc"))  # Start watching in the background
    server.start()
