# Project Documentation

## Overview
This project consists of a **server** and a **broker**, each running in separate Docker containers. The server handles API endpoints to transmit data, while the broker makes scheduled requests to the server API endpoints for data.

## Project Structure
### Compression
- **Source Code:** Located in `/workspaces/${WORKSPACE}/server`
- **Functions:**
  - `Draco` encoder version `1.5.7`
  - Compress `.ply` to `.drc`
### Server
- **Source Code:** Located in `/workspaces/${WORKSPACE}/server`
- **Functions:**
  - Handles API requests
  - Serves broker requests via HTTP
  - Zip requested data and stream response to brokers (e.g., `.drc -> .zip -> stream`)
  - Runs `pydash.py` with specified host, port, and data directory
- **Notes**
  - Prepare your data in corresponding directories
  - Prepare directory format:
    - Folder to save your processed data (`.drc, .ply, .zip, etc.`): `./media/<your project name>/bar`
    - Folder to store sent data: `./media/<your project name>/archive`

### Broker
- **Source Code:** Located in `/workspaces/${WORKSPACE}/broker`
- **Functions:**
  - Makes scheduled API requests to the server
  - Stores downloads in a specified directory/database
  - Runs `scheduled_request.py` with specified API and parameters

### Decompression
- **Source Code:** Located in `/workspaces/${WORKSPACE}/server`
- **Functions:**
  - `Draco` decoder version `1.5.7`
  - Decompress `.zip -> .drc -> .ply`

## Interaction Diagram
Below is a simplified diagram of the interaction between the server and broker:

```
                `Jetson`               |    `Network`     |           `Cloud server`
                                       |                  |                                     
+--------------+       +----------+    |   API Requests   |   +----------+      +--------------+ 
|              |       |          | <--|------------------|-- |          |      |              |
| Compression  |       |  Server  | ---|------------------|-> |  Broker  |      |Decompression |
|              |       |          |    |  API Responses   |   |          |      |              |
+--------------+       +----------+    |                  |   +----------+      +--------------+
       |                    ↑          |                  |        |                    ↑
       |                    |          |  `network can    |        |                    |
       |     +----------+   |          |  be wifi, etc.`  |        |     +----------+   |
       |     |          |   |          |                  |        |     |          |   |
       |---> | Database |---|          |                  |        |---> | Database |---|
             |          |              |                  |              |          |   
             +----------+              |                  |              +----------+  

  - The compression gets input data --> compresses them to .drc --> store to database
  - The broker sends scheduled requests to the server.
  - The server processes requests --> checks database --> zips .drc data --> streams data.
  - The broker stores the received data in the database.
  - The decompression checks database --> unzips .zip to get .drc data --> decompresses .drc to .ply data
```

## Environment Variables
Create a `.env` file in the root directory with the following variables:

```ini
# .env file

WORKSPACE=fastapi-file-streaming
PROJECT=head

# Compression/Decompression environment variables
COMPRESSION_MOUNT=/workspaces/fastapi-file-streaming/test/compression/data
DEPRESSION_MOUNT=/workspaces/fastapi-file-streaming/test/decompression/data

# Server environment variables
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SERVER_MOUNT=/workspaces/fastapi-file-streaming/test/media

# Broker environment variables
INTERVAL=2
API_URL=http://server:8080/stream
EXT=drc
BROKER_MOUNT=/workspaces/fastapi-file-streaming/test/media
```

## Docker Compose Configuration
### Services
- **Server**
  - Builds from `/workspaces/${WORKSPACE}/server`
  - Mounts media directories (`host to container`) where the processed data are available
  - Exposes `SERVER_PORT`
- **Broker**
  - Builds from `/workspaces/${WORKSPACE}/broker`
  - Mounts a download directory (`host to container`) to store received data
  - Depends on the `server` service

### Networks
- **my_network**: A bridge network connecting the server and broker

### Volumes
- **server_mount**: Persistent volume for server media files
- **broker_mount**: Persistent volume for broker downloads

## Usage
### Build and Start Containers
Run the following command to build and start the services:
```sh
docker-compose up
```

### Stop Containers
To stop the running containers:
```sh
docker-compose down
```

### View Logs
To check logs for each service:
```sh
docker-compose logs -f server
```
```sh
docker-compose logs -f broker
```

## Troubleshooting
- Ensure `.env` variables are correctly set.
- Check mounted volume paths.
- Verify network settings using `docker network ls`.
- Restart containers if needed:
  ```sh
  docker-compose restart
  ```

## Supports
- End2end for `.ply` input data.
- Compression and Decompression: `.ply <--> .drc, .zip <--> .drc`.
- Database: directory mount.
- Sofware-based technology: `fastapi` `StreamingResponse`

## Futures
- Upgrade database: `redis, etc.`

## Notes
- Current test is running on `1` `ubuntu 22.04 server`
- When testing with more `ubuntu 22.04 server`,
  - it needs to modify corresponding `API_URL` to ensure communications between `server` and `broker`.
  - modify docker compose as required per testing purpose.
## License
This project is licensed under the MIT License.



