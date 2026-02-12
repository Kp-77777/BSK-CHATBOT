# BSK API Installation Guide (Linux VPS)

This guide is aligned with your current `docker-compose.yml`:
- `app` container (FastAPI) on host port `8001`
- `mongodb` container in compose
- Ollama is pre-installed and running on the VPS host (not in compose)

Choose one deployment path:
- **A) Tar file + direct Docker run**
- **B) Git pull on VPS + Docker Compose up**

---

## A) Tar File + Direct Docker Run

### 1) Prerequisites
- Docker installed and running
- Ollama installed on VPS host
- Models pulled on host:
```
ollama pull llama3.1:latest
ollama pull mxbai-embed-large:latest
```

### 2) Transfer and load image
From local machine:
```
scp bsk-chatapi.tar user@VPS_IP:/home/user/
```
On VPS:
```
docker load -i /home/user/bsk-chatapi.tar
docker images | grep bsk-chatapi
```

### 3) Create runtime folders
```
sudo mkdir -p /opt/bsk/chroma /opt/bsk/logs
sudo chown -R $USER:$USER /opt/bsk
```

### 4) Create `.env`
```
nano /opt/bsk/.env
```
Use:
```
MONGODB_URI=mongodb://<MONGO_HOST>:27017
MONGO_DB_NAME=bsk_assistant
OLLAMA_BASE_URL=http://<VPS_HOST_IP>:11434
CHROMA_PERSIST_DIRECTORY=./db/chroma
ENVIRONMENT=production
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=350
```

### 5) Run API container
```
docker run -d --name bsk-chatapi \
  -p 9001:8000 \
  --env-file /opt/bsk/.env \
  -v /opt/bsk/chroma:/app/db/chroma \
  -v /opt/bsk/logs:/app/logs \
  bsk-chatapi
```

### 6) Test
```
curl http://VPS_IP:9001/
```
Swagger:
```
http://VPS_IP:9001/docs
```

---

## B) Git Pull on VPS + Docker Compose Up

This path uses your current compose architecture:
- MongoDB in compose
- App in compose
- Ollama on VPS host

### 1) Prerequisites
- Docker + Docker Compose installed
- Git installed
- Ollama installed on VPS host and running

Install Ollama if needed:
```
curl -fsSL https://ollama.com/install.sh | sh
```
Start:
```
ollama serve
```
Pull models:
```
ollama pull llama3.1:latest
ollama pull mxbai-embed-large:latest
```

### 2) Clone or pull repository
First time:
```
cd /opt
git clone <YOUR_REPO_URL> bsk
cd /opt/bsk
```
Existing repo:
```
cd /opt/bsk
git pull origin <YOUR_BRANCH>
```

### 3) Update compose for host Ollama URL
Edit:
```
nano /opt/bsk/docker-compose.yml
```
Set:
```
OLLAMA_BASE_URL: http://<VPS_HOST_IP>:11434
```

Also ensure:
```
MONGODB_URI: mongodb://mongodb:27017
```

### 4) Start with compose
```
cd /opt/bsk
docker compose up -d --build
```

### 5) Verify services
```
docker compose ps
docker logs -f bsk-app
```

### 6) Test API
```
curl http://VPS_IP:8001/
```
Swagger:
```
http://VPS_IP:8001/docs
```

### 7) Update after new commits
```
cd /opt/bsk
git pull origin <YOUR_BRANCH>
docker compose up -d --build
```

---

## Troubleshooting

### Port conflict
If `8001` is in use, change host port mapping in compose from:
```
8001:8000
```
to another port (for example `9010:8000`) and restart compose.

### Ollama unreachable from container
- Do not use `localhost` in compose env for Ollama.
- Use host IP:
```
OLLAMA_BASE_URL=http://<VPS_HOST_IP>:11434
```
- Confirm from host:
```
curl http://localhost:11434/api/tags
```

### MongoDB unreachable in compose
Ensure app env uses compose service name:
```
MONGODB_URI=mongodb://mongodb:27017
```

### Persisted data check
MongoDB data:
- volume `bsk_mongodb_data`

Chroma and logs:
- volumes mapped in app service (`/app/db/chroma`, `/app/logs`)

