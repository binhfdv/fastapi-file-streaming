# Project Documentation

## Overview
This project consists of a **server** and a **client**, each running in separate Docker containers. The server handles API endpoints to transmit data, while the client makes scheduled requests to the server API endpoints for data.

## Project Structure
### Server
- **Source Code:** Located in `/workspaces/${WORKSPACE}/server`
- **Functions:**
  - Handles API requests
  - Serves client requests via HTTP
  - Zip requested data and stream response to clients
  - Runs `pydash.py` with specified host, port, and data directory
- **Notes**
  - Prepare your data in corresponding directories
  - Prepare directory format:
    - Folder to save your processed data (`.drc, .ply, .zip, etc.`): `./media/<your project name>/bar`
    - Folder to store sent data: `./media/<your project name>/archive`

### Client
- **Source Code:** Located in `/workspaces/${WORKSPACE}/client`
- **Functions:**
  - Makes scheduled API requests to the server
  - Processes received data
  - Stores downloads in a specified directory
  - Runs `scheduled_request.py` with specified API and parameters

## Interaction Diagram
Below is a simplified diagram of the interaction between the server and client:

```
+-----------+        API Requests        +-----------+
|  Client   | -------------------------> |  Server   |
|           | <------------------------- |           |
|           |       API Responses        |           |
+-----------+                             +-----------+

  - The client sends scheduled requests to the server.
  - The server processes requests and returns data.
  - The client stores the received data in the mounted volume.
```

## Environment Variables
Create a `.env` file in the root directory with the following variables:

```ini
# .env file

WORKSPACE=fastapi-file-streaming
PROJECT=head
# Server environment variables
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SERVER_MOUNT=/workspaces/fastapi-file-streaming/test/media

# Client environment variables
INTERVAL=2 # request interval in seconds
API_URL=http://server:8080/stream
EXT=drc # file extension for downloads
CLIENT_MOUNT=/workspaces/fastapi-file-streaming/test/media
```

## Docker Compose Configuration
### Services
- **Server**
  - Builds from `/workspaces/${WORKSPACE}/server`
  - Mounts media directories (`host to container`) where the processed data are available
  - Exposes `SERVER_PORT`
- **Client**
  - Builds from `/workspaces/${WORKSPACE}/client`
  - Mounts a download directory (`host to container`) to store received data
  - Depends on the `server` service

### Networks
- **my_network**: A bridge network connecting the server and client

### Volumes
- **server_mount**: Persistent volume for server media files
- **client_mount**: Persistent volume for client downloads

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
docker-compose logs -f client
```

## Troubleshooting
- Ensure `.env` variables are correctly set.
- Check mounted volume paths.
- Verify network settings using `docker network ls`.
- Restart containers if needed:
  ```sh
  docker-compose restart
  ```

## License
This project is licensed under the MIT License.



