# Changelog

All notable changes to MySQLens will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-19

### 🎉 Initial Release

#### Added
- **Core Features**
  - Real-time MySQL performance monitoring
  - Live query analysis with execution metrics
  - Database vitals dashboard (QPS, buffer pool, connections)
  - Connection management for remote MySQL databases
  - Encrypted credential storage

- **Index Analysis**
  - Unused index detection
  - Redundant index identification
  - Missing index recommendations
  - Index statistics and size analysis

- **AI-Powered Analysis**
  - Multi-provider LLM support (OpenAI, Gemini, DeepSeek, Ollama)
  - Intelligent query optimization suggestions
  - Context-aware performance recommendations
  - Schema-aware analysis

- **Health Monitoring**
  - Comprehensive database health scans
  - Table fragmentation detection
  - Configuration issue identification
  - MySQL best practice recommendations
  - Buffer pool efficiency analysis
  - Connection pool monitoring

- **User Interface**
  - Modern dashboard built with Next.js 15
  - Responsive design with Tailwind CSS
  - Beautiful UI components from Shadcn UI
  - Real-time data visualization
  - Dark mode support (planned)

- **Backend API**
  - FastAPI-based REST API
  - Comprehensive API documentation (Swagger/ReDoc)
  - Async MySQL connections with aiomysql
  - Connection pooling for optimal performance
  - SQLite-based metadata storage

- **DevOps**
  - Docker and Docker Compose support
  - Production-ready configuration
  - Environment-based configuration
  - Makefile for common tasks
  - Health check endpoints

- **Documentation**
  - Comprehensive README
  - Architecture documentation
  - API endpoint reference
  - Deployment guide
  - Contributing guidelines

#### Security
- Encrypted credential storage
- Secure password handling
- CORS configuration for API security
- Environment variable-based secrets management

#### Performance
- Async/await patterns throughout
- Connection pooling
- Efficient query batching
- Optimized Docker builds
- Frontend and backend caching

---

## [Unreleased]

### Added
- **Local LLM Support with Ollama** (Inspired by OptiSchema-Slim)
  - Complete Ollama provider implementation for privacy-first AI analysis
  - Support for multiple Ollama models (llama3.2, sqlcoder:7b, deepseek-coder-v2)
  - Zero data egress - all LLM processing happens locally
  - No API costs or rate limits for AI features
  - Offline capability for air-gapped environments
  - Comprehensive Ollama setup guide (OLLAMA_SETUP.md)
  - Test script for verifying Ollama integration (test_ollama.py)

- **Docker Compose Improvements**
  - **Ollama as default LLM provider** in all compose files
  - New `docker-compose.ollama.yml` for running Ollama in Docker
  - Automatic model downloading on first start
  - GPU support configuration for Ollama container
  - Better organized environment variables with clear comments
  - Production and development configs both default to Ollama

- **Documentation Improvements**
  - Enhanced README with detailed Ollama setup instructions
  - Comprehensive QUICK_START.md with 5-minute setup guide
  - OLLAMA_SETUP.md with model comparisons, hardware requirements, and troubleshooting
  - Docker Compose configurations clearly documented
  - Reorganized documentation structure for better clarity

- **Configuration Updates**
  - Updated .env.example with Ollama as default provider
  - Better model selection guidance
  - Docker networking configuration for local LLM
  - Support for both Docker and local development setups

### Changed
- **Docker Compose V2**: Updated all commands from `docker-compose` to `docker compose` (V2)
  - Updated all documentation (README, QUICK_START, OLLAMA_SETUP, etc.)
  - Updated Makefile to use `docker compose`
  - Setup script now detects and supports both V1 and V2
  - Added compatibility notes in documentation

- **Docker Compose Configuration**
  - Changed default LLM provider from "gemini" to "ollama" in all compose files
  - Added OLLAMA_MODEL environment variable (defaults to llama3.2:latest)
  - Reorganized environment variables with clear sections and comments
  - Changed production defaults: BACKEND_RELOAD=false, DEBUG=false, ENVIRONMENT=production
  - TOP_QUERIES_LIMIT increased from 10 to 50 for better analysis

- **LLM Configuration**
  - LLM provider factory now prioritizes Ollama for privacy
  - Default Ollama model updated to llama3.2:latest
  - Reorganized .env.example to highlight local LLM options
  - Enhanced error messages for LLM connection issues

- **Project Identity**
  - Fixed project name in Makefile and setup.sh (was "OptiSchema-MySQL", now "MySQLens")

### Planned Features
- [ ] Historical performance tracking
- [ ] Query execution plan visualization
- [ ] Custom alert rules and notifications
- [ ] Query comparison and A/B testing
- [ ] Export reports (PDF, CSV)
- [ ] Multi-database support
- [ ] User authentication and authorization
- [ ] Role-based access control
- [ ] WebSocket for real-time updates
- [ ] Query history and saved analyses
- [ ] Custom dashboard widgets
- [ ] Dark mode
- [ ] Mobile-responsive improvements
- [ ] PostgreSQL support (separate tool)
- [ ] Monitoring multiple MySQL instances simultaneously
- [ ] Integration with Prometheus/Grafana
- [ ] Slack/Discord notifications
- [ ] Automated optimization recommendations
- [ ] Scheduled health scans
- [ ] API rate limiting
- [ ] Audit logging

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to contribute to MySQLens.

## Support

- Report bugs: [GitHub Issues](https://github.com/a-kash-singh/mysqlens/issues)
- Feature requests: [GitHub Discussions](https://github.com/a-kash-singh/mysqlens/discussions)

---

[1.0.0]: https://github.com/a-kash-singh/mysqlens/releases/tag/v1.0.0

