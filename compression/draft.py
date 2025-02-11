import redis
import os

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Metadata hash name
METADATA_HASH = "compression_streaming_data"

def store_file_in_stream(file_path, chunk_size=1024):
    filename = os.path.basename(file_path)  # Use the filename as the key
    stream_name = f"file_chunks:{filename}"  # Unique stream name

    with open(file_path, 'rb') as f:
        chunk_count = 0
        while chunk := f.read(chunk_size):
            r.xadd(stream_name, {"chunk": chunk})
            chunk_count += 1

    # Store metadata (filename → stream name & chunk count)
    r.hset(METADATA_HASH, filename, f"{stream_name}|{chunk_count}")

    print(f"File '{filename}' stored in Redis.")
    return filename  # Return filename for reference

def list_stored_files():
    files = r.hgetall(METADATA_HASH)
    if not files:
        print("No files found in Redis.")
        return []

    stored_files = []
    for filename, metadata in files.items():
        stream_name, chunk_count = metadata.decode().split("|")
        stored_files.append({"filename": filename.decode(), "stream_name": stream_name, "chunks": chunk_count})

    return stored_files

def retrieve_any_stored_file():
    files = list_stored_files()
    if not files:
        return
    
    print("\nAvailable files:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file['filename']} (Chunks: {file['chunks']})")

    for i in range(len(files)):
        filename = files[i]['filename']
        output_path = f"retrieved_{filename}"
        retrieve_file_from_stream(filename, output_path)
        print(f"File retrieved as '{output_path}'.")

def retrieve_file_from_stream(filename, output_path):
    metadata = r.hget(METADATA_HASH, filename)
    if not metadata:
        print("File not found in Redis!")
        return

    stream_name, chunk_count = metadata.decode().split("|")
    chunk_count = int(chunk_count)

    with open(output_path, 'wb') as f:
        chunks = r.xrange(stream_name)  # Get all chunks from stream
        for _, data in chunks:
            f.write(data[b'chunk'])

    print(f"File '{filename}' reconstructed as '{output_path}'.")



# Example usage
store_file_in_stream("/workspaces/fastapi-file-streaming/test/media/head/archive/3.drc", chunk_size=512)

stored_files = list_stored_files()
for file in stored_files:
    print(f"Filename: {file['filename']}, Chunks: {file['chunks']}")

retrieve_any_stored_file()
