# BSK API Installation Guide (Docker Image Tar)

This guide assumes you already built the Docker image on your laptop and have a `bsk-chatapi.tar` file. Your VPS is **Linux-based**.

Choose **one** of the two deployment methods:
- **A) Direct Docker run** (most common)
- **B) Docker Compose** (runs app + optional MongoDB/Ollama containers)

---

## A) Direct Docker Run (Recommended for external MongoDB/Ollama)

### 1) Prerequisites on the VPS
- Docker installed and running
- Network access to MongoDB
- Open firewall for the port you will expose (example: 9001)

### 2) Ollama location (choose one)
**A. Ollama on the same VPS host**
- Install Ollama and start the service.
  ```
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  Start Ollama (if not already running):
  ```
  ollama serve
  ```
- Pull models:
```
ollama pull llama3.1:latest
ollama pull mxbai-embed-large:latest
```
Verify:
```
ollama list
```

**B. Ollama on a different server**
- Ensure the VPS can reach it (firewall, routing).
- You will set `OLLAMA_BASE_URL` to that server’s IP.

### 3) Transfer the image to the VPS
```
scp bsk-chatapi.tar user@VPS_IP:/home/user/
```

### 4) Load the image on the VPS
```
docker load -i /home/user/bsk-chatapi.tar
```
Verify:
```
docker images | grep bsk-chatapi
```

### 5) Create project directories on the VPS
```
sudo mkdir -p /opt/bsk/chroma /opt/bsk/logs
sudo chown -R $USER:$USER /opt/bsk
```

### 6) Create the `.env` file on the VPS
Create `/opt/bsk/.env` with correct values.

**If MongoDB and Ollama are on the VPS host:**
```
MONGODB_URI=mongodb://VPS_IP:27017
MONGO_DB_NAME=bsk_assistant

OLLAMA_BASE_URL=http://VPS_IP:11434

CHROMA_PERSIST_DIRECTORY=./db/chroma
ENVIRONMENT=production
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=350
```

**If MongoDB or Ollama are on another server:**
- Replace `VPS_IP` with the external server IP/hostname.

### 6.1) Edit the `.env` file
Open and edit values:
```
nano /opt/bsk/.env
```
Save and exit:
- Press `CTRL+O`, then `Enter`
- Press `CTRL+X`

### 7) Run the container (API only)
Example using host port **9001** (container listens on 8000):
```
docker run -d --name bsk-chatapi \
  -p 9001:8000 \
  --env-file /opt/bsk/.env \
  -v /opt/bsk/chroma:/app/db/chroma \
  -v /opt/bsk/logs:/app/logs \
  bsk-chatapi
```

### 8) Test
```
curl http://VPS_IP:9001/
```
Swagger UI:
```
http://VPS_IP:9001/docs
```

---

## B) Docker Compose (Runs app + MongoDB + Ollama containers)

Use this only if you want MongoDB + Ollama **containerized** on the VPS.

### 1) Prerequisites
- Docker and Docker Compose installed
- Ports 8000, 27017, 11434 available (or change host ports)

### 2) Update docker-compose.yml
- Keep only API port (remove 8501)
- Keep `MONGODB_URI: mongodb://mongodb:27017`
- Keep `OLLAMA_BASE_URL: http://ollama:11434`
- Ensure volumes for `/app/db/chroma` and `/app/logs`

### 3) Bring it up
```
docker compose up -d
```

### 4) Pull Ollama models inside the Ollama container
```
docker exec -it bsk-ollama ollama pull llama3.1:latest
docker exec -it bsk-ollama ollama pull mxbai-embed-large:latest
```

### 5) Test
```
curl http://VPS_IP:8000/
```

---

## Common Issues and Fixes

### Port conflict
If you see “bind: address already in use”, choose another host port:
```
docker run -d --name bsk-chatapi \
  -p 9010:8000 \
  --env-file /opt/bsk/.env \
  -v /opt/bsk/chroma:/app/db/chroma \
  -v /opt/bsk/logs:/app/logs \
  bsk-chatapi
```

### MongoDB or Ollama unreachable
Symptoms:
- “Cannot connect to Ollama…”
- “MongoDB connection failed…”

Fix:
- Ensure services are running.
- Ensure firewall allows access.
- Use correct IPs in `.env`. Do NOT use `localhost` unless the service is in the same container.

### Persisted data missing after restart
Ensure you used volume mounts:
```
-v /opt/bsk/chroma:/app/db/chroma
-v /opt/bsk/logs:/app/logs
```

### View logs
```
docker logs -f bsk-chatapi
```

---

## Stop / Remove / Update

Stop:
```
docker stop bsk-chatapi
```

Remove:
```
docker rm bsk-chatapi
```

Update with a new tar:
```
docker stop bsk-chatapi
docker rm bsk-chatapi
docker load -i /home/user/new-bsk-chatapi.tar
docker run -d --name bsk-chatapi \
  -p 9001:8000 \
  --env-file /opt/bsk/.env \
  -v /opt/bsk/chroma:/app/db/chroma \
  -v /opt/bsk/logs:/app/logs \
  bsk-chatapi
```
