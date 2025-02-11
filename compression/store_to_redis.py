import sys
import redis
import os

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_COMPRESSION_HOST", "redis")  # Default to 'redis' (container name in Docker network)
REDIS_PORT = int(os.getenv("REDIS_COMPRESSION_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Connect to Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=False)
    r.ping()  # Test connection
    print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError:
    print("Failed to connect to Redis. Check if the Redis container is running.")
    sys.exit(1)

# Metadata hash name
METADATA_HASH = "compression_streaming_data"

def store_file_in_stream(file_path, chunk_size=1024):
    """Stores a file in Redis Stream in chunks."""
    filename = os.path.basename(file_path)  # Extract filename
    stream_name = f"file_chunks:{filename}"  # Unique Redis stream name

    try:
        with open(file_path, 'rb') as f:
            chunk_count = 0
            while chunk := f.read(chunk_size):
                r.xadd(stream_name, {"chunk": chunk})
                chunk_count += 1

        # Store metadata (filename → stream name & chunk count)
        r.hset(METADATA_HASH, filename, f"{stream_name}|{chunk_count}")

        print(f"File '{filename}' stored in Redis Stream '{stream_name}' with {chunk_count} chunks.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error storing file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python store_to_redis.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    store_file_in_stream(file_path)
