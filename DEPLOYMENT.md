# Deployment Guide for MySQLens

This guide covers various deployment scenarios for MySQLens.

## Table of Contents

- [Docker Compose (Recommended)](#docker compose-recommended)
- [Manual Installation](#manual-installation)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Kubernetes](#kubernetes)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Docker Compose (Recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/a-kash-singh/MySQLens.git
cd MySQLens

# Create environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Production Deployment with Docker Compose

```bash
# Use production compose file
docker compose -f docker compose.yml up -d

# Scale services (if needed)
docker compose up -d --scale mysqlens-api=2
```

## Manual Installation

### Backend Setup

```bash
# Install Python 3.11+
python --version

# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key_here
export BACKEND_HOST=0.0.0.0
export BACKEND_PORT=8080

# Run the application
python main.py
```

### Frontend Setup

```bash
# Install Node.js 20+
node --version

# Install dependencies
cd frontend
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL=http://localhost:8080
export BACKEND_URL=http://localhost:8080

# Build and start
npm run build
npm start

# Or for development
npm run dev
```

## Production Deployment

### Prerequisites

- Docker & Docker Compose
- Reverse proxy (Nginx or Traefik)
- SSL certificate (Let's Encrypt)
- Domain name

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker compose-plugin

# Create application directory
sudo mkdir -p /opt/mysqlens
cd /opt/mysqlens
```

### 2. Configuration

```bash
# Clone repository
git clone https://github.com/a-kash-singh/MySQLens.git .

# Create production .env
cat > .env << EOF
# LLM Configuration
GEMINI_API_KEY=your_production_key
LLM_PROVIDER=gemini

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Frontend Configuration
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NODE_ENV=production
EOF

# Set permissions
chmod 600 .env
```

### 3. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/mysqlens

# Frontend
server {
    listen 80;
    listen [::]:80;
    server_name mysqlens.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mysqlens.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/mysqlens.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mysqlens.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Proxy to frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy to backend API
    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API (optional separate domain)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.mysqlens.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.mysqlens.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mysqlens.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/mysqlens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d mysqlens.yourdomain.com -d api.mysqlens.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 5. Start Services

```bash
cd /opt/mysqlens
docker compose up -d

# Verify
docker compose ps
docker compose logs -f
```

### 6. Systemd Service (Optional)

```bash
# Create systemd service
sudo nano /etc/systemd/system/mysqlens.service
```

```ini
[Unit]
Description=MySQLens
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/mysqlens
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mysqlens
sudo systemctl start mysqlens
sudo systemctl status mysqlens
```

## Cloud Deployment

### AWS (EC2)

```bash
# Launch EC2 instance (Ubuntu 22.04)
# t3.medium or larger recommended

# Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# Follow production deployment steps above

# Security Group Rules:
# - Port 22 (SSH) from your IP
# - Port 80 (HTTP) from 0.0.0.0/0
# - Port 443 (HTTPS) from 0.0.0.0/0
# - Port 3306 (MySQL) from instance private IP only
```

### Google Cloud (Compute Engine)

```bash
# Create VM instance
gcloud compute instances create mysqlens \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium \
    --boot-disk-size=20GB \
    --zone=us-central1-a

# SSH into instance
gcloud compute ssh mysqlens --zone=us-central1-a

# Follow production deployment steps
```

### DigitalOcean

```bash
# Create Droplet (Ubuntu 22.04, 2GB RAM minimum)

# SSH into droplet
ssh root@your-droplet-ip

# Follow production deployment steps
```

## Kubernetes

### Deployment YAML

```yaml
# mysqlens-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mysqlens

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysqlens-config
  namespace: mysqlens
data:
  BACKEND_HOST: "0.0.0.0"
  BACKEND_PORT: "8080"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: mysqlens-secrets
  namespace: mysqlens
type: Opaque
stringData:
  GEMINI_API_KEY: "your-api-key-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysqlens-api
  namespace: mysqlens
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mysqlens-api
  template:
    metadata:
      labels:
        app: mysqlens-api
    spec:
      containers:
      - name: api
        image: your-registry/mysqlens-api:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: mysqlens-config
        - secretRef:
            name: mysqlens-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysqlens-ui
  namespace: mysqlens
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mysqlens-ui
  template:
    metadata:
      labels:
        app: mysqlens-ui
    spec:
      containers:
      - name: ui
        image: your-registry/mysqlens-ui:latest
        ports:
        - containerPort: 3000
        env:
        - name: BACKEND_URL
          value: "http://mysqlens-api:8080"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: mysqlens-api
  namespace: mysqlens
spec:
  selector:
    app: mysqlens-api
  ports:
  - port: 8080
    targetPort: 8080

---
apiVersion: v1
kind: Service
metadata:
  name: mysqlens-ui
  namespace: mysqlens
spec:
  selector:
    app: mysqlens-ui
  ports:
  - port: 3000
    targetPort: 3000

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mysqlens-ingress
  namespace: mysqlens
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - mysqlens.yourdomain.com
    secretName: mysqlens-tls
  rules:
  - host: mysqlens.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: mysqlens-api
            port:
              number: 8080
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mysqlens-ui
            port:
              number: 3000
```

Deploy:
```bash
kubectl apply -f mysqlens-deployment.yaml
kubectl get pods -n mysqlens
kubectl logs -f deployment/mysqlens-api -n mysqlens
```

## Configuration

### Environment Variables

**Required:**
- `GEMINI_API_KEY` or `OPENAI_API_KEY`: API key for LLM
- `LLM_PROVIDER`: Provider to use (gemini, openai, deepseek)

**Optional:**
- `BACKEND_HOST`: Backend host (default: 0.0.0.0)
- `BACKEND_PORT`: Backend port (default: 8080)
- `ENVIRONMENT`: Environment (development, production)
- `DEBUG`: Debug mode (true, false)
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `CACHE_TTL`: Cache TTL in seconds (default: 3600)

### MySQL Configuration

Ensure `performance_schema` is enabled in MySQL:

```ini
# /etc/mysql/my.cnf or /etc/my.cnf
[mysqld]
performance_schema = ON
```

## Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8080/health

# Check connection status
curl http://localhost:8080/api/connection/status

# Check database health
curl http://localhost:8080/api/health/scan
```

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f mysqlens-api
docker compose logs -f mysqlens-ui

# Save logs to file
docker compose logs > logs.txt
```

### Metrics

Monitor these metrics:
- API response times
- Database connection pool status
- LLM API success rate
- Error rates
- Memory usage
- CPU usage

## Backup

### Backup SQLite Database

```bash
# Backup recommendations database
docker compose exec mysqlens-api sqlite3 /app/mysqlens.db .dump > backup.sql

# Restore
cat backup.sql | docker compose exec -T mysqlens-api sqlite3 /app/mysqlens.db
```

## Troubleshooting

### Can't Connect to MySQL

1. Check MySQL is accessible
2. Verify `performance_schema` is enabled
3. Check firewall rules
4. Verify credentials

### Services Won't Start

```bash
# Check logs
docker compose logs

# Rebuild images
docker compose build --no-cache

# Remove old containers
docker compose down -v
docker compose up -d
```

### High Memory Usage

- Reduce connection pool size
- Decrease cache size
- Limit query sample size

### API Errors

```bash
# Check backend logs
docker compose logs mysqlens-api

# Verify environment variables
docker compose exec mysqlens-api env | grep API_KEY

# Test API directly
curl http://localhost:8080/api/metrics/vitals
```

---

For more help, see the [README](README.md) or open an issue on GitHub.

