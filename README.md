# MySQLens

<div align="center">

🔍 **AI-powered MySQL performance optimization tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

**See clearly. Optimize confidently.**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Architecture](#architecture) • [Contributing](#contributing)

</div>

---

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

---

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

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- MySQL 8.0+ (with `performance_schema` enabled)
- (Optional) LLM API keys for AI features

### 1. Clone the Repository

```bash
git clone https://github.com/a-kash-singh/mysqlens.git
cd mysqlens
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# LLM Provider Configuration (choose one or more)
LLM_PROVIDER=gemini                    # Options: openai, gemini, deepseek, ollama

# API Keys (add the ones you want to use)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
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

## 📚 Documentation

- **[Architecture](./ARCHITECTURE.md)** - System design and technical details
- **[API Endpoints](./API_ENDPOINTS.md)** - Complete API reference
- **[Deployment Guide](./DEPLOYMENT.md)** - Production deployment instructions
- **[Contributing](./CONTRIBUTING.md)** - How to contribute to MySQLens

---

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

### Ollama (Local)
```bash
# Install Ollama: https://ollama.ai
ollama pull llama2
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

## 📊 Screenshots

### Dashboard
![Dashboard showing real-time metrics, QPS, buffer pool, and connections](https://via.placeholder.com/800x400?text=MySQLens+Dashboard)

### Query Analysis
![Top slow queries with execution times and AI recommendations](https://via.placeholder.com/800x400?text=Query+Analysis)

### Index Recommendations
![Unused, redundant, and missing index analysis](https://via.placeholder.com/800x400?text=Index+Recommendations)

---

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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by [OptiSchema-Slim](https://github.com/a-kash-singh/optischema-slim) for PostgreSQL
- Built with ❤️ using modern web technologies
- AI-powered by OpenAI, Google, DeepSeek, and Ollama
- UI components from [Shadcn UI](https://ui.shadcn.com/)

---

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/a-kash-singh/mysqlens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/a-kash-singh/mysqlens/discussions)
- **Twitter**: [@a-kash-singh](https://twitter.com/a-kash-singh)

---

## ⭐ Star History

If you find MySQLens helpful, please consider giving it a star! ⭐

---

<div align="center">

**Built with 🔍 for better MySQL performance**

[⬆ Back to Top](#mysqlens)

</div>
