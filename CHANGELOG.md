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

