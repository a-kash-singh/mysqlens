# MySQLens

<div align="center">

🔍 **AI-powered MySQL performance optimization tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Inspired by OptiSchema](https://img.shields.io/badge/Inspired%20by-OptiSchema--Slim-purple.svg)](https://github.com/arnab2001/Optischema-Slim)

**See clearly. Optimize confidently.**

[Features](#features) • [Quick Start](#quick-start) • [LLM Setup](#llm-provider-setup) • [Documentation](#documentation) • [Architecture](#architecture) • [Contributing](#contributing)

</div>

---

## 💡 Inspiration

This project is inspired by [**OptiSchema-Slim**](https://github.com/arnab2001/Optischema-Slim) - an excellent PostgreSQL performance optimization tool. We've adapted the concept for MySQL with enhanced features:

- ✅ **Local LLM Support**: Complete privacy with Ollama integration
- ✅ **MySQL-Specific**: Tailored for MySQL 8.0+ with `performance_schema`
- ✅ **Multiple Model Support**: Choose from llama3.2, sqlcoder:7b, and more
- ✅ **Zero Data Egress**: All AI processing happens locally (when using Ollama)

Special thanks to [@arnab2001](https://github.com/arnab2001) for the innovative approach to database optimization!

---

## 📑 Table of Contents

- **[👉 Quick Start Guide](./QUICK_START.md)** - Get started in 5 minutes!
- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start) (condensed version)
- [Configuration](#configuration)
- [LLM Provider Setup](#llm-provider-setup)
  - [Ollama (Local - Recommended)](#ollama-local-llm---recommended-for-privacy)
  - [OpenAI](#openai)
  - [Google Gemini](#google-gemini)
  - [DeepSeek](#deepseek)
- [Screenshots](#screenshots)
- [Development](#development)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Contact & Support](#contact--support)

---

<a id="overview"></a>

## 📖 Overview

MySQLens is a production-ready MySQL database performance optimization tool that combines real-time monitoring with AI-powered analysis. It helps database administrators and developers identify performance bottlenecks, optimize queries, and maintain healthy MySQL databases.

### Why MySQLens?

- 🎯 **Real-time Insights** - Live monitoring of queries, connections, and database vitals
- 🤖 **AI-Powered Analysis** - Leverages multiple LLM providers (OpenAI, Gemini, DeepSeek, Ollama) for intelligent query optimization
- 🔍 **Index Intelligence** - Automatically detects unused, redundant, and missing indexes
- 📊 **Beautiful Dashboard** - Modern, responsive UI built with Next.js 15 and Shadcn UI
- 🔒 **Secure** - Encrypted credential storage and secure connections
- 🐳 **Docker-Ready** - One-command deployment with Docker Compose
- 🌐 **Remote MySQL Support** - Connect to any MySQL instance (local, cloud, RDS, etc.)
- 🔐 **Privacy-First** - Run AI analysis completely locally with Ollama (no data leaves your machine)

---

<a id="features"></a>

## ✨ Features

### Performance Monitoring
- **Live Query Analysis** - Track slow queries, execution times, and resource usage
- **Database Vitals** - Monitor QPS, buffer pool hit ratio, connections, and more
- **Performance Schema Integration** - Leverages MySQL's built-in performance_schema

### Index Optimization
- **Unused Index Detection** - Identify indexes that consume space but aren't used
- **Redundant Index Analysis** - Find duplicate and overlapping indexes
- **Missing Index Recommendations** - Suggest indexes for queries performing full table scans

### AI-Powered Insights
- **Multi-Provider Support** - Choose from OpenAI, Google Gemini, DeepSeek, or local Ollama
- **Query Optimization** - Get AI-powered recommendations for query improvements
- **Context-Aware Analysis** - Considers schema, indexes, and execution plans

### Health Monitoring
- **Comprehensive Health Scans** - Check table fragmentation, configuration issues, and more
- **Proactive Alerts** - Identify potential problems before they become critical
- **Best Practice Recommendations** - MySQL configuration and schema design suggestions

---

<a id="quick-start"></a>

## 🚀 Quick Start

**Want to get started fast?** 👉 See the **[Quick Start Guide](./QUICK_START.md)** for a complete 5-minute setup including Ollama!

### TL;DR - Get Running in 5 Minutes

```bash
# 1. Install Ollama (for local AI - optional)
brew install ollama && ollama serve
ollama pull llama3.2:latest

# 2. Clone and configure
git clone https://github.com/a-kash-singh/mysqlens.git
cd mysqlens
echo "LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:latest" > .env

# 3. Start MySQLens
docker compose up -d

# 4. Open browser
open http://localhost:3000
```

That's it! Connect to your MySQL and start optimizing.

### Detailed Setup

#### Prerequisites
- Docker and Docker Compose
- MySQL 8.0+ (with `performance_schema` enabled)
- (Optional) LLM API keys for AI features OR Ollama for local AI

#### 1. Clone the Repository

```bash
git clone https://github.com/a-kash-singh/mysqlens.git
cd mysqlens
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# LLM Provider Configuration (choose one)
LLM_PROVIDER=ollama                     # Options: ollama, openai, gemini, deepseek

# Ollama (Local LLM - No API key needed!)
OLLAMA_BASE_URL=http://host.docker.internal:11434  # For Docker
OLLAMA_MODEL=llama3.2:latest                        # Model name

# Cloud API Keys (optional - only if not using Ollama)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Quick Ollama Setup:**
```bash
# Install and start Ollama
brew install ollama  # macOS (see README for other platforms)
ollama serve

# Pull a model (in a new terminal)
ollama pull llama3.2:latest

# Verify it's running
curl http://localhost:11434/api/tags
```

### 3. Start the Application

```bash
# Start all services (Ollama on host - recommended)
docker compose up -d

# View logs
docker compose logs -f
```

> **Note:** We use `docker compose` (V2, built into Docker CLI) instead of the older `docker-compose` (V1). If you have an older Docker installation, use `docker-compose` with a hyphen. The setup script (`./setup.sh`) automatically detects which version you have.

**Optional: Run Ollama in Docker**

If you prefer to run Ollama as a container instead of on your host:
```bash
# Use the ollama compose extension
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d

# This will:
# - Run Ollama in a container
# - Automatically download llama3.2:latest model
# - Configure MySQLens to use the Ollama container
```

### 4. Access the Dashboard

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **API Health**: http://localhost:8080/api/health

### 5. Connect to Your MySQL Database

1. Click "Connect to Database" on the dashboard
2. Enter your MySQL connection details:
   - **Host**: Your MySQL host (e.g., `localhost`, `mysql.example.com`, RDS endpoint)
   - **Port**: 3306 (default)
   - **Username**: Your MySQL user
   - **Password**: Your password (encrypted at rest)
   - **Database**: Database name to analyze

**Note**: For remote MySQL connections from Docker, use the actual hostname or IP (not `localhost`). For host machine MySQL, use `host.docker.internal` on macOS/Windows.

---

<a id="documentation"></a>

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](./QUICK_START.md)** ⭐ - Complete 5-minute setup guide (includes Ollama)
- **[Ollama Setup](./OLLAMA_SETUP.md)** - Deep dive into local LLM setup and troubleshooting

### Technical Documentation
- **[Architecture](./ARCHITECTURE.md)** - System design and technical details
- **[API Endpoints](./API_ENDPOINTS.md)** - Complete API reference
- **[Deployment Guide](./DEPLOYMENT.md)** - Production deployment instructions

### Reference
- **[DB Config Guide](./DB_CONFIG_GUIDE.md)** - Advanced database configuration
- **[Contributing](./CONTRIBUTING.md)** - How to contribute to MySQLens
- **[Changelog](./CHANGELOG.md)** - All notable changes

---

<a id="architecture"></a>

## 🏗️ Architecture

MySQLens uses a modern, scalable architecture:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Next.js 15    │─────▶│   FastAPI       │─────▶│   MySQL DB      │
│   Frontend      │      │   Backend       │      │   (Your DB)     │
│   (Port 3000)   │◀─────│   (Port 8080)   │◀─────│                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
                                │
                                ▼
                         ┌──────────────┐
                         │  LLM APIs    │
                         │  (AI Power)  │
                         └──────────────┘
```

**Tech Stack:**
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11+, aiomysql, Pydantic
- **Database**: MySQL 8.0+ (performance_schema required)
- **AI**: OpenAI GPT-4, Google Gemini, DeepSeek, Ollama
- **Deployment**: Docker, Docker Compose

---

<a id="configuration"></a>

## 🔧 Configuration

### MySQL User Permissions

MySQLens requires the following permissions:

```sql
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'your_user'@'%';
GRANT SELECT ON performance_schema.* TO 'your_user'@'%';
GRANT SELECT ON information_schema.* TO 'your_user'@'%';
GRANT SELECT ON mysql.* TO 'your_user'@'%';
FLUSH PRIVILEGES;
```

### Remote MySQL Configuration

For remote connections, ensure:

1. **MySQL bind-address** is set to `0.0.0.0` (not `127.0.0.1`)
2. **Firewall** allows connections on port 3306
3. **User permissions** allow connections from your host (`'user'@'%'` or specific IP)
4. **Performance schema** is enabled: `performance_schema = ON` in my.cnf

---

<a id="llm-provider-setup"></a>

## 🤖 LLM Provider Setup

### OpenAI
```bash
OPENAI_API_KEY=sk-...
```
Get your key from: https://platform.openai.com/api-keys

### Google Gemini
```bash
GEMINI_API_KEY=AIza...
```
Get your key from: https://makersuite.google.com/app/apikey

### DeepSeek
```bash
DEEPSEEK_API_KEY=sk-...
```
Get your key from: https://platform.deepseek.com/

### Ollama (Local LLM - Recommended for Privacy)

Ollama allows you to run LLMs locally without sending data to external APIs. This is perfect for privacy-conscious users and offline environments.

**Setup Steps:**

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Windows - Download from https://ollama.com/download
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Pull a Recommended Model**
   ```bash
   # For general SQL analysis (recommended)
   ollama pull llama3.2:latest

   # For SQL-specific tasks (larger, more specialized)
   ollama pull sqlcoder:7b

   # Lightweight option (faster, less capable)
   ollama pull llama3.2:1b
   ```

4. **Configure MySQLens**

   In your `.env` file:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434  # For Docker
   # OR
   OLLAMA_BASE_URL=http://localhost:11434              # For local development
   OLLAMA_MODEL=llama3.2:latest                        # Or sqlcoder:7b
   ```

**Model Recommendations:**
- **llama3.2:latest** (4.7GB) - Best balance of speed and quality for SQL analysis
- **sqlcoder:7b** (4.1GB) - Specialized for SQL, trained on SQL optimization tasks
- **llama3.2:1b** (1.3GB) - Lightweight, good for basic analysis on limited hardware
- **deepseek-coder-v2** (8.9GB) - Excellent for complex query optimization

**Testing Your Setup:**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Test with a simple query
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:latest",
  "prompt": "Explain what a database index is"
}'
```

**Benefits of Local LLM:**
- Complete data privacy - your schema and queries never leave localhost
- No API costs or rate limits
- Works offline
- Faster response times (no network latency)
- Full control over model selection

---

<a id="screenshots"></a>

## 📊 Screenshots

### Dashboard
![Dashboard showing real-time metrics, QPS, buffer pool, and connections](https://via.placeholder.com/800x400?text=MySQLens+Dashboard)

### Query Analysis
![Top slow queries with execution times and AI recommendations](https://via.placeholder.com/800x400?text=Query+Analysis)

### Index Recommendations
![Unused, redundant, and missing index analysis](https://via.placeholder.com/800x400?text=Index+Recommendations)

---

<a id="development"></a>

## 🛠️ Development

### Local Development Setup

1. **Backend Development:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

2. **Frontend Development:**
```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Using Makefile

```bash
make help          # Show all available commands
make build         # Build all Docker images
make up            # Start all services
make down          # Stop all services
make logs          # View logs
make restart       # Restart all services
```

---

<a id="contributing"></a>

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<a id="license"></a>

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

<a id="acknowledgments"></a>

## 🙏 Acknowledgments

- Inspired by [OptiSchema-Slim](https://github.com/arnab2001/Optischema-Slim) for PostgreSQL
- Built with ❤️ using modern web technologies
- AI-powered by OpenAI, Google, DeepSeek, and Ollama
- UI components from [Shadcn UI](https://ui.shadcn.com/)

---

<a id="contact--support"></a>

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/a-kash-singh/mysqlens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/a-kash-singh/mysqlens/discussions)
- **Twitter**: [@a-kash-singh](https://twitter.com/a-kash-singh)

---

## ⭐ Star History

If you find MySQLens helpful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=a-kash-singh/mysqlens&type=Date)](https://star-history.com/#a-kash-singh/mysqlens&Date)

---

<div align="center">

**Built with 🔍 for better MySQL performance**

**Inspired by [OptiSchema-Slim](https://github.com/arnab2001/Optischema-Slim)**

[⬆ Back to Top](#mysqlens)

</div>
