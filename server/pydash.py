from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import Response
import os
import time as T
import logging
import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

# Create a router
router = APIRouter()

class DASHServer():
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, media_path: str = "./media", cache=None):
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

        self.cache = cache

    def get_extension(self, path):
        return os.path.splitext(path)[1]

    def load_file(self, path):
        t_start = T.time()

        data = None
        if self.cache is not None:
            data = self.cache.get(path)

        if data is None:
            logging.debug("Cache miss")
            try:
                with open(path, 'rb') as file:
                    data = file.read()
            except FileNotFoundError:
                return None
            
            if self.cache is not None:
                self.cache.set(path, data)
        else:
            logging.debug("Cache hit")

        delta = T.time() - t_start
        logging.debug(f"Response Time \"{path}\" {delta:.2f}ms")
        return data

    def start(self):
        asyncio.run(serve(self.app, self.config))


# Define API Routes using `@router`
@router.get("/media")
async def media_mpd():
    filename = os.path.join("./media", "foo", "mpd.xml")
    
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="MPD file not found")

    with open(filename, "rb") as file:
        data = file.read()

    return Response(content=data, media_type="application/dash+xml")


@router.get("/media/{name}/{representation}/{segment}")
async def media_segment(name: str, representation: str, segment: str):
    filename = os.path.join("./media", name, representation, segment)

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
