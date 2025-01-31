from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import Response
import os
import time as T
import logging
import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import shutil


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

        # Register MIME types
        mimetypes.add_type('pointcloud/ply', '.ply')
        mimetypes.add_type('pointcloud/drc', '.drc')
        mimetypes.add_type('pointcloud/mpeg-vpcc', '.vpcc')
        mimetypes.add_type('pointcloud/mpeg-gpcc', '.gpcc')
        mimetypes.add_type('application/zip', '.zip')
    

    def create_zip(self, dext: str = "drc", project: str = "foo"):
        """Create a ZIP file containing all XML files."""
        zip_path = os.path.join(self.media_path, project, "bar", f"latest_{dext}_data.zip")
        
        # Remove the existing zip file if it exists
        if os.path.exists(zip_path):
            os.remove(zip_path)

        latest_files = [f for f in os.listdir(self.media_path) if f.endswith(dext)]
        if not latest_files:
            return None  # No files to zip
        
        # Create ZIP archive
        with shutil.ZipFile(zip_path, 'w') as zipf:
            for file in latest_files:
                file_path = os.path.join(self.media_path, file)
                zipf.write(file_path, arcname=file)

        return zip_path
    

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


# Start the server
if __name__ == "__main__":
    server = DASHServer()
    server.start()
