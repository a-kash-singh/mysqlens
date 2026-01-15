---
layout: default
title: API Reference
permalink: /docs/api/
---

# MySQLens API Endpoints

## Base URL
- Local: `http://localhost:8080`
- Docker: `http://mysqlens-api:8080`

## Connection Endpoints

### GET /api/connection/status
Get current connection status.

**Response:**
```json
{
  "connected": true,
  "host": "mysql-host.example.com",
  "port": 3306,
  "database": "your_database",
  "version": "8.0.x",
  "user": "your_user"
}
```

### POST /api/connection/connect
Establish connection to MySQL database.

**Request:**
```json
{
  "host": "mysql-host.example.com",
  "port": 3306,
  "user": "your_user",
  "password": "your_password",
  "database": "your_database"
}
```

### POST /api/connection/disconnect
Disconnect from MySQL database.

### POST /api/connection/test
Test connection without saving.

## Metrics Endpoints

### GET /api/metrics/vitals
Get database vitals (QPS, buffer pool, connections).

**Response:**
```json
{
  "success": true,
  "data": {
    "qps": { "value": 296.38, "status": "ok" },
    "buffer_pool_hit_ratio": { "value": 100.0, "status": "ok" },
    "active_connections": { "value": 382, "status": "ok" },
    "max_connections": { "value": 3000, "status": "ok" }
  }
}
```

### GET /api/metrics/queries?limit=50
Get top slow queries.

**Query Parameters:**
- `limit` (optional): Number of queries to return (default: 50)

### GET /api/metrics/db-info
Get database information and statistics.

### POST /api/metrics/reset
Reset performance schema statistics.

## Analysis Endpoints

### GET /api/analysis/indexes/unused?min_size_mb=1.0
Get unused index recommendations.

**Query Parameters:**
- `min_size_mb` (optional): Minimum index size in MB (default: 1.0)

### GET /api/analysis/indexes/redundant
Get redundant index recommendations.

### GET /api/analysis/indexes/missing
Get missing index recommendations.

### GET /api/analysis/indexes/full
Run full index analysis (unused, redundant, missing).

### GET /api/analysis/indexes/stats
Get database index statistics.

## Health Endpoints

### GET /api/health
Get API health status.

### GET /api/health/scan
Run comprehensive health scan.

## Settings Endpoints

### GET /api/settings/llm-providers
Get available LLM providers.

**Response:**
```json
{
  "success": true,
  "data": {
    "available": ["openai", "gemini", "deepseek"],
    "current": "gemini"
  }
}
```

### GET /api/settings/config
Get current configuration (non-sensitive).

## Documentation

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Notes

- All endpoints return JSON responses
- Most endpoints require an active database connection
- Error responses follow the format:
  ```json
  {
    "success": false,
    "message": "Error message",
    "error": "Detailed error"
  }
  ```

---

<div align="center">
<a href="{{ '/' | relative_url }}">← Back to Home</a>
</div>
