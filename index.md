---
layout: default
title: MySQLens - AI-Powered MySQL Performance Optimization
---

<div align="center">

<h1>🔍 MySQLens</h1>

<p><strong>AI-powered MySQL performance optimization tool</strong></p>

<p>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
<a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-blue.svg" alt="Docker"></a>
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-green.svg" alt="Python"></a>
<a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-15-black.svg" alt="Next.js"></a>
<a href="https://github.com/arnab2001/Optischema-Slim"><img src="https://img.shields.io/badge/Inspired%20by-OptiSchema--Slim-purple.svg" alt="Inspired by OptiSchema"></a>
</p>

<p><strong>See clearly. Optimize confidently.</strong></p>

<p>
<a href="#features">Features</a> •
<a href="#quick-start">Quick Start</a> •
<a href="{{ '/docs/quick-start/' | relative_url }}">Docs</a> •
<a href="https://github.com/a-kash-singh/mysqlens">GitHub</a>
</p>

</div>

---

## 💡 What is MySQLens?

MySQLens is a **production-ready MySQL performance optimization tool** that combines real-time monitoring with AI-powered analysis. It helps database administrators and developers:

- 🎯 **Identify slow queries** and performance bottlenecks
- 🤖 **Get AI-powered optimization recommendations** using OpenAI, Gemini, or local Ollama
- 🔍 **Detect unused and redundant indexes** wasting disk space
- 📊 **Monitor database health** in real-time

<a id="features"></a>

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🔐 Privacy-First** | Run AI analysis locally with Ollama - no data leaves your machine |
| **🎯 Real-time Monitoring** | Live metrics for QPS, connections, buffer pool, and more |
| **🤖 Multi-LLM Support** | OpenAI, Gemini, DeepSeek, or local Ollama |
| **📈 Index Intelligence** | Detect unused, duplicate, and missing indexes |
| **🐳 Docker-Ready** | One-command deployment with Docker Compose |
| **🌐 Remote MySQL** | Connect to any MySQL instance (local, cloud, RDS) |

<a id="quick-start"></a>

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/a-kash-singh/mysqlens.git
cd mysqlens

# Configure LLM (Ollama for privacy, or cloud APIs)
echo "LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:latest" > .env

# Start MySQLens
docker compose up -d

# Open in browser
open http://localhost:3000
```

**📖 Need more details?** Check out the [complete Quick Start Guide]({{ '/docs/quick-start/' | relative_url }}).

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Next.js 15    │─────▶│   FastAPI       │─────▶│   MySQL DB      │
│   Frontend      │      │   Backend       │      │   (Your DB)     │
│   (Port 3000)   │◀─────│   (Port 8080)   │◀─────│                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  LLM APIs    │
                         │  (AI Power)  │
                         └──────────────┘
```

<a id="documentation"></a>

## 📚 Documentation

- 🚀 [Quick Start Guide]({{ '/docs/quick-start/' | relative_url }}) - Get started in 5 minutes
- 🤖 [Ollama Setup]({{ '/docs/ollama-setup/' | relative_url }}) - Local LLM configuration
- 🏗️ [Architecture]({{ '/docs/architecture/' | relative_url }}) - System design and tech stack
- 📡 [API Reference]({{ '/docs/api/' | relative_url }}) - Complete API documentation

**More on GitHub:**
- 📖 [Full README](https://github.com/a-kash-singh/mysqlens/blob/main/README.md) - Complete documentation
- 🚢 [Deployment Guide]({{ '/docs/deployment/' | relative_url }}) - Production deployment
- 📋 [Contributing](https://github.com/a-kash-singh/mysqlens/blob/main/CONTRIBUTING.md) - How to contribute

## 🙏 Acknowledgments

This project is inspired by [**OptiSchema-Slim**](https://github.com/arnab2001/Optischema-Slim) - an excellent PostgreSQL performance optimization tool by [@arnab2001](https://github.com/arnab2001).

---

<div align="center">

**Built with 🔍 for better MySQL performance**

<p>
<a href="https://github.com/a-kash-singh/mysqlens">⭐ View on GitHub</a> •
<a href="https://github.com/a-kash-singh/mysqlens/issues">🐛 Report Bug</a> •
<a href="https://github.com/a-kash-singh/mysqlens/discussions">💬 Discussions</a>
</p>

<p>
<a href="#top">⬆ Back to Top</a>
</p>

</div>
