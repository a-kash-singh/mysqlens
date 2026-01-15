---
layout: default
title: Quick Start Guide
permalink: /docs/quick-start/
---

# 🚀 MySQLens Quick Start Guide

Get MySQLens up and running in **5 minutes** with local AI-powered MySQL optimization!

---

## Prerequisites

- **Docker** and **Docker Compose** installed
- **MySQL 8.0+** with `performance_schema` enabled
- **8GB+ RAM** (16GB recommended for local LLM)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/a-kash-singh/mysqlens.git
cd mysqlens
```

---

## Step 2: Choose Your LLM Provider

### Option A: Local LLM with Ollama (Recommended - Private & Free)

**Why Ollama?**
- ✅ Complete privacy - data never leaves your machine
- ✅ No API costs
- ✅ Works offline
- ✅ No rate limits

**Install Ollama:**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - Download from https://ollama.com/download
```

**Start Ollama and pull a model:**

```bash
# Start Ollama (in one terminal)
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2:latest  # Recommended (4.7GB)
# OR
ollama pull sqlcoder:7b      # SQL-specialized (4.1GB)
# OR
ollama pull llama3.2:1b      # Lightweight (1.3GB)

# Verify installation
ollama list
```

**Configure MySQLens:**

Create `.env` file in project root:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:latest
```

### Option B: Cloud LLM Providers

If you prefer cloud providers, create `.env`:

```bash
# Choose one:
LLM_PROVIDER=gemini          # or openai, deepseek

# Add your API key:
GEMINI_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
# OR
DEEPSEEK_API_KEY=your_key_here
```

**Get API keys:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Gemini**: https://makersuite.google.com/app/apikey
- **DeepSeek**: https://platform.deepseek.com/

---

## Step 3: Start MySQLens

```bash
# Start all services
docker compose up -d

# Check if everything is running
docker compose ps

# View logs (optional)
docker compose logs -f
```

> **Docker Compose Note:** This guide uses `docker compose` (V2, built into modern Docker). If you have an older installation, use `docker-compose` with a hyphen instead. Our setup script (`./setup.sh`) automatically detects and uses the correct version.

**Expected output:**
```
✓ mysqlens-frontend running
✓ mysqlens-api running
```

**Check logs for Ollama (if using):**
```bash
docker compose logs backend | grep -i ollama
# Should see: "Creating Ollama provider for local LLM"
```

---

## Step 4: Access the Dashboard

Open your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs

---

## Step 5: Connect to Your MySQL Database

### Option A: Connect via UI (Easiest)

1. Click **"Connect to Database"** button
2. Enter your MySQL credentials:
   ```
   Host: your-mysql-host.com
   Port: 3306
   User: your_username
   Password: your_password
   Database: your_database
   ```
3. Click **"Connect"**

**For Docker users:**
- If MySQL is on your host machine, use: `host.docker.internal` (macOS/Windows)
- For Linux Docker, use: `172.17.0.1` or your host IP

### Option B: Save Connection in Config File

Create `db-config.json` in project root:

```json
{
  "connections": [
    {
      "name": "Production",
      "host": "your-mysql-host.com",
      "port": 3306,
      "user": "your_username",
      "password": "your_password",
      "database": "your_database",
      "is_default": true
    }
  ],
  "auto_connect": true
}
```

Then restart:
```bash
docker compose restart backend
```

**Security:** Set proper permissions:
```bash
chmod 600 db-config.json
```

---

## ✅ Verification Checklist

After connecting, you should see:

- [x] **Dashboard loads** with real-time metrics
- [x] **QPS (Queries Per Second)** displayed
- [x] **Buffer Pool Hit Ratio** shown
- [x] **Active Connections** count
- [x] **Top Slow Queries** list populated
- [x] **AI Analysis** button available (if LLM configured)

---

## 🎯 Next Steps

### 1. Test AI Analysis (if using Ollama)

```bash
cd backend
python3 test_ollama.py
```

Should see: `✅ All tests passed!`

### 2. Explore Features

- **Index Analysis**: Check for unused, redundant, and missing indexes
- **Query Optimization**: Get AI-powered recommendations for slow queries
- **Health Scans**: Run comprehensive database health checks
- **Real-time Monitoring**: Watch live performance metrics

### 3. Configure MySQL User Permissions

For full functionality, grant these permissions:

```sql
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'your_user'@'%';
GRANT SELECT ON performance_schema.* TO 'your_user'@'%';
GRANT SELECT ON information_schema.* TO 'your_user'@'%';
GRANT SELECT ON mysql.* TO 'your_user'@'%';
FLUSH PRIVILEGES;
```

---

## 🐛 Troubleshooting

### Ollama Connection Issues

**Problem:** "Cannot connect to Ollama"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve

# Check if model is installed
ollama list

# Pull model if missing
ollama pull llama3.2:latest
```

**For Docker on Linux:**
```bash
# Update .env to use host IP instead of host.docker.internal
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

### MySQL Connection Issues

**Problem:** "Connection refused"

```bash
# 1. Check MySQL is running and accessible
mysql -h your-mysql-host.com -u your_user -p

# 2. Verify MySQL allows remote connections
# In my.cnf:
bind-address = 0.0.0.0  # Not 127.0.0.1

# 3. Check firewall
sudo ufw allow 3306
```

**Problem:** "Access denied"

```sql
-- Check user permissions
SHOW GRANTS FOR 'your_user'@'%';

-- Grant required permissions (see above)
```

### Container Issues

**Problem:** Containers won't start

```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
docker compose down
docker compose up -d --build

# Check Docker resources (8GB+ RAM needed)
docker stats
```

### Performance Schema Not Enabled

```sql
-- Check if enabled
SHOW VARIABLES LIKE 'performance_schema';

-- If OFF, add to my.cnf and restart MySQL:
[mysqld]
performance_schema = ON
```

---

## 📖 Additional Resources

- **Ollama Deep Dive**: [Ollama Setup]({{ '/docs/ollama-setup/' | relative_url }}) - Comprehensive guide
- **Architecture**: [Architecture]({{ '/docs/architecture/' | relative_url }}) - Technical details
- **API Reference**: [API Reference]({{ '/docs/api/' | relative_url }}) - All endpoints
- **Deployment**: [Deployment Guide]({{ '/docs/deployment/' | relative_url }}) - Production setup
- **DB Config**: [DB Config Guide]({{ '/docs/db-config-guide/' | relative_url }}) - Advanced config

---

## 🎓 Learn More

### Ollama Model Selection

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| **llama3.2:latest** | 4.7GB | General use (recommended) | ⭐⭐⭐⭐ |
| **sqlcoder:7b** | 4.1GB | SQL optimization | ⭐⭐⭐ |
| **llama3.2:1b** | 1.3GB | Limited resources | ⭐⭐⭐⭐⭐ |
| **deepseek-coder-v2** | 8.9GB | Best quality | ⭐⭐⭐ |

See [Ollama Setup]({{ '/docs/ollama-setup/' | relative_url }}) for detailed comparisons.

### Multiple Database Connections

Edit `db-config.json` to manage multiple databases:

```json
{
  "connections": [
    {
      "name": "Production",
      "host": "prod.example.com",
      "is_default": true
    },
    {
      "name": "Staging",
      "host": "staging.example.com",
      "is_default": false
    }
  ]
}
```

Switch via API:
```bash
curl -X POST http://localhost:8080/api/connection/connect-saved/Staging
```

---

## 🔧 Useful Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart

# Stop everything
docker compose down

# Start with build
docker compose up -d --build

# Check status
docker compose ps

# Access backend shell
docker compose exec backend bash

# Test Ollama integration
docker compose exec backend python test_ollama.py
```

---

## 💡 Pro Tips

1. **Use Ollama for privacy** - Keep sensitive data local
2. **Start with llama3.2:latest** - Good balance of speed and quality
3. **Enable auto_connect** - Saves time on restarts
4. **Set up saved connections** - Manage multiple databases easily
5. **Run health scans regularly** - Catch issues early
6. **Check index recommendations** - Easy performance wins

---

## 🎉 You're All Set!

MySQLens is now running and ready to optimize your MySQL database!

**What's Next?**
1. Run your first AI query analysis
2. Check for unused indexes
3. Perform a health scan
4. Monitor real-time performance

**Need Help?**
- **Issues**: https://github.com/a-kash-singh/mysqlens/issues
- **Discussions**: https://github.com/a-kash-singh/mysqlens/discussions
- **Documentation**: See links above

---

<div align="center">

**Happy Optimizing! 🔍**

**Inspired by [OptiSchema-Slim](https://github.com/arnab2001/Optischema-Slim)**

</div>
