from logger import CustomLogger
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import Response, FileResponse, StreamingResponse
import os
import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import shutil
import zipfile
from datetime import datetime
import argparse
import redis


REDIS_HOST = os.getenv("REDIS_COMPRESSION_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_COMPRESSION_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

METADATA_HASH = "compression_streaming_data"

# Create a router
router = APIRouter()
log = CustomLogger()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=False)


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
    

    def create_zip_stream(self, project: str = "foo", ext: str = "drc"):
        """Create a ZIP file containing all latest files."""
        bar_path = os.path.join(self.media_path, project, "bar")
        archive_path = os.path.join(self.media_path, project, "archive")

        log.info(f"Creating project: {project}'s directory if not existed")
        os.makedirs(bar_path, exist_ok=True)
        os.makedirs(archive_path, exist_ok=True)

        try:
            latest_files = [f for f in os.listdir(bar_path) if f.endswith(ext)]
        except Exception as e:
            log.error(e)
            log.debug("... project may not be available")
            log.debug("... check media path and project")
            latest_files = []

        if not latest_files:
            log.info("No new files to zip")
            return None, None
        
        # Generate timestamped filename
        log.info(f"Generating zip file for {len(latest_files)} {ext} files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{ext}_{len(latest_files)}files_{timestamp}.zip"
        zip_path = os.path.join(bar_path, zip_filename)
              
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in latest_files:
                file_path = os.path.join(bar_path, file)
                zipf.write(file_path, arcname=file)
            log.info("Zip file is ready")
        
        for file in latest_files:
            log.info(f"Moving {ext} files to archive for storage after zipped")
            shutil.move(os.path.join(bar_path, file), os.path.join(archive_path, file))

        return zip_filename, zip_path
    

    def retrieve_file_from_stream(self, filename, output_path):
        metadata = r.hget(METADATA_HASH, filename)
        if not metadata:
            log.warning("File not found in Redis!")
            return

        stream_name, chunk_count = metadata.decode().split("|")
        chunk_count = int(chunk_count)
        
        with open(output_path, 'wb') as f:
            chunks = r.xrange(stream_name)  # Get all chunks from stream
            for _, data in chunks:
                f.write(data[b'chunk'])

        log.info(f"File '{filename}' reconstructed as '{output_path}'.")
        
        r.delete(stream_name)  # Delete the Redis stream
        r.hdel(METADATA_HASH, filename)  # Remove metadata entry
        log.info(f"File '{filename}' removed from Redis after restoration.")


    def list_stored_files(self):
        files = r.hgetall(METADATA_HASH)
        if not files:
            log.info("No files found in Redis.")
            return []

        stored_files = []
        for filename, metadata in files.items():
            stream_name, chunk_count = metadata.decode().split("|")
            stored_files.append({"filename": filename.decode(), "stream_name": stream_name, "chunks": chunk_count})

        return stored_files


    def create_zip_stream_redis(self, project: str = "foo", ext: str = "drc"):
        files = self.list_stored_files()
        if not files:
            log.info("Server --- No files found in Redis")
            return None, None
        
        log.info("\nAvailable files:")
        for i, file in enumerate(files):
            log.info(f"{i + 1}. {file['filename']} (Chunks: {file['chunks']})")

        bar_path = os.path.join(self.media_path, project, "bar")
        log.info(f"Creating project: {project}'s directory if not existed")
        os.makedirs(bar_path, exist_ok=True)

        for i in range(len(files)):
            filename = files[i]['filename']
            output_path = os.path.join(bar_path, filename)
            self.retrieve_file_from_stream(filename, output_path)

        zip_filename, zip_path = self.create_zip_stream(project, ext)
        
        return zip_filename, zip_path
    

    def remove_zip(self, zip_path: str) -> None:
        log.info("Zip files is being removed after streamed")
        os.remove(zip_path)


    def check_types(self, ext: str) -> bool:
        if ext in ["ply", "drc", "vpcc", "gpcc", "zip"]: return True
        else: return False
        

    def start(self):
        log.info("Streaming server is starting...")
        asyncio.run(serve(self.app, self.config))
        log.info("Server stopped.")


server = DASHServer()


# Define API Routes using `@router`
@router.get("/media/{project}")
async def media_mpd(project: str):
    """Response with mpd file to client when requested"""
    filename = os.path.join("./media", project, "mpd.xml")
    
    if not os.path.exists(filename):
        log.warning("MPD file not found")
        raise HTTPException(status_code=404, detail="MPD file not found")

    with open(filename, "rb") as file:
        data = file.read()

    return Response(content=data, media_type="application/dash+xml")


@router.get("/media/{project}/{representation}/{segment}")
async def media_segment(project: str, representation: str, segment: str):
    """Response with file (drc, ply, etc.) to client when requested"""
    filename = os.path.join("./media", project, representation, segment)

    content_type = mimetypes.guess_type(filename, strict=False)[0]
    if content_type is None:
        log.warning(f"Unsupported file type .{segment.split(".")[-1]}")
        raise HTTPException(status_code=406, detail="Unsupported file type")
    
    if not os.path.exists(filename):
        log.warning(f"Segment {segment} file not found")
        raise HTTPException(status_code=404, detail=f"{segment} file not found")

    with open(filename, "rb") as file:
        data = file.read()

    return Response(content=data, media_type=content_type)


@router.get("/fetch/{project}/{ext}")
async def download_latest_files(project: str, ext: str):
    """Response data (zip) to client when requested"""
    # server = DASHServer()

    if server.check_types(ext) == False:
        log.warning(f"Unsupported file type .{ext}")
        raise HTTPException(status_code=406, detail="Unsupported file type")
    
    _, zip_path = server.create_zip_stream(project, ext)

    if not zip_path:
        log.warning(f"No .{ext} files available")
        raise HTTPException(status_code=404, detail=f"No .{ext} files available")

    return FileResponse(zip_path, filename=os.path.basename(zip_path), media_type="application/zip")


@router.get("/stream/{project}/{ext}")
async def stream_for_zip(project: str, ext: str, background_tasks: BackgroundTasks):
    """Stream data (zip) to client when requested."""
    # server = DASHServer()

    if server.check_types(ext) == False:
        log.warning(f"Unsupported file type .{ext}")
        raise HTTPException(status_code=406, detail="Unsupported file type")
    
    _, zip_path = server.create_zip_stream_redis(project, ext)

    if not zip_path:
        log.info(f"No .{ext} files available")
        raise HTTPException(status_code=404, detail=f"No .{ext} files available")
    
    def iterfile():
        with open(zip_path, mode="rb") as fzip:
            yield from fzip
    
    # remove zip after streamed
    background_tasks.add_task(server.remove_zip, zip_path)

    headers = {'Content-Disposition': f'attachment; filename="{zip_path.split('/')[-1]}"'}
    return StreamingResponse(iterfile(),
                             headers=headers,
                             media_type="application/zip")

# Start the server
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--datadir", default="./media")
    args = parser.parse_args()

    log.info(f"host: {args.host} port: {args.port} media path: {args.datadir}")
    server = DASHServer(host=args.host, port=args.port, media_path=args.datadir)
    asyncio.run(server.start())
