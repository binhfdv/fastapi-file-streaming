from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import Response, FileResponse, StreamingResponse
import os
import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import shutil
import zipfile
from datetime import datetime

# Create a router
router = APIRouter()

class DASHServer():
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, media_path: str = "./media"):
        self.media_path = media_path

        self.config = Config()
        self.config.bind = f"{host}:{port}"

        # FastAPI app with router
        self.app = FastAPI()
        self.app.include_router(router)  # Attach the router

        # self.subscribers = set()  # Store connected clients

        # Register MIME types
        mimetypes.add_type('pointcloud/ply', '.ply')
        mimetypes.add_type('pointcloud/drc', '.drc')
        mimetypes.add_type('pointcloud/mpeg-vpcc', '.vpcc')
        mimetypes.add_type('pointcloud/mpeg-gpcc', '.gpcc')
        mimetypes.add_type('application/zip', '.zip')
    

    async def watch_project_and_send_zip(self, project: str = "foo", ext: str = "drc"):
        """Continuously watches for new files and streams ZIP when detected."""
        bar_path = os.path.join(self.media_path, project, "bar")

        known_files = set(os.listdir(bar_path))  # Track existing files

        while True:
            current_files = set(os.listdir(bar_path))
            new_files = current_files - known_files

            
            print(current_files)


            if new_files:
                known_files = current_files  # Update known files

                # Create ZIP and send to clients
                zip_filename, zip_path = self.create_zip_stream(project, ext)

                print("-------zip filename: ", zip_filename)
                print("-------zip path: ", zip_path)

                if zip_filename:# and self.subscribers:
                    yield zip_path  # Notify clients

            await asyncio.sleep(2)  # Check every 2 seconds


    def create_zip_stream(self, project: str = "foo", ext: str = "drc"):
        """Create a ZIP file containing all latest files."""
        bar_path = os.path.join(self.media_path, project, "bar")
        archive_path = os.path.join(self.media_path, project, "archive")

        latest_files = [f for f in os.listdir(bar_path) if f.endswith(ext)]
        if not latest_files:
            return None, None  # No files to zip
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{ext}_{len(latest_files)}files_{timestamp}.zip"
        zip_path = os.path.join(bar_path, zip_filename)
              
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in latest_files:
                file_path = os.path.join(bar_path, file)
                zipf.write(file_path, arcname=file)

        for file in latest_files:
            shutil.move(os.path.join(bar_path, file), os.path.join(archive_path, file))

        return zip_filename, zip_path
    

    def start(self):
        asyncio.run(serve(self.app, self.config))

# Define API Routes using `@router`
@router.get("/media/{project}")
async def media_mpd(project: str):
    filename = os.path.join("./media", project, "mpd.xml")
    
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="MPD file not found")

    with open(filename, "rb") as file:
        data = file.read()

    return Response(content=data, media_type="application/dash+xml")


@router.get("/media/{project}/{representation}/{segment}")
async def media_segment(project: str, representation: str, segment: str):
    filename = os.path.join("./media", project, representation, segment)

    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Segment file not found")

    with open(filename, "rb") as file:
        data = file.read()

    content_type = mimetypes.guess_type(filename, strict=False)[0]
    if content_type is None:
        raise HTTPException(status_code=406, detail="Unsupported file type")

    return Response(content=data, media_type=content_type)


@router.get("/stream/{project}/{ext}")
async def download_latest_files(project: str, ext: str):
    server = DASHServer()
    _, zip_path = server.create_zip_stream(project, ext)

    if not zip_path:
        raise HTTPException(status_code=404, detail=f"No {ext} files available")

    return FileResponse(zip_path, filename=os.path.basename(zip_path), media_type="application/zip")


@router.get("/subscribe/{project}/{ext}")
async def subscribe_for_zip(project: str, ext: str):
    """Client subscribes to automatic ZIP file delivery when new files appear."""
    server = DASHServer()
    return StreamingResponse(server.watch_project_and_send_zip(project, ext), media_type="application/zip")


# Start the server
if __name__ == "__main__":
    server = DASHServer()
    asyncio.run(server.start())
