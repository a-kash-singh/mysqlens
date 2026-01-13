# MySQLens Architecture

## System Overview

MySQLens is a local-first, AI-powered MySQL performance optimization tool. It follows a **Collect → Analyze → Recommend** pipeline with strict privacy and safety guarantees.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Next.js Frontend (Port 3000)              │    │
│  │  • React 19 with App Router                           │    │
│  │  • SWR for data fetching                              │    │
│  │  • Tailwind CSS for styling                           │    │
│  │  • Real-time metrics visualization                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ▲                                     │
│                            │ HTTP/REST API                       │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              FastAPI Backend (Port 8080)               │    │
│  │                                                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │   Routers    │  │   Services   │  │  LLM       │  │    │
│  │  │  - Connection│  │  - Metrics   │  │  - Gemini  │  │    │
│  │  │  - Metrics   │  │  - Schema    │  │  - OpenAI  │  │    │
│  │  │  - Analysis  │  │  - LLM       │  │  - DeepSeek│  │    │
│  │  │  - Health    │  │  - Health    │  │            │  │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │    │
│  │                                                        │    │
│  │  ┌──────────────┐  ┌──────────────┐                  │    │
│  │  │  Connection  │  │   Storage    │                  │    │
│  │  │   Manager    │  │   (SQLite)   │                  │    │
│  │  └──────────────┘  └──────────────┘                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ▲                                     │
│                            │ aiomysql                            │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                User's MySQL Database                   │    │
│  │         (with performance_schema enabled)              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

External: LLM APIs (Gemini, OpenAI, DeepSeek)
```

## Core Components

### 1. Frontend Layer (Next.js 15)

**Technology Stack:**
- Next.js 15 with App Router
- React 19
- TypeScript
- Tailwind CSS
- SWR for data fetching
- Axios for HTTP requests

**Key Components:**
- `ConnectionForm`: Database connection interface
- `Dashboard`: Main analytics dashboard
- Real-time metrics visualization
- Query analysis interface

**Features:**
- Server-side rendering (SSR)
- Client-side data fetching with SWR
- Responsive design
- Dark mode support
- Auto-refresh for live metrics

### 2. Backend Layer (FastAPI)

**Technology Stack:**
- FastAPI 0.104.1
- Python 3.11+
- AsyncIO for non-blocking operations
- Pydantic for data validation
- aiomysql for MySQL async connections

**Architecture Patterns:**
- **Async/Await**: All I/O operations are non-blocking
- **Dependency Injection**: Used for services and connections
- **Repository Pattern**: Clean separation of data access
- **Service Layer**: Business logic separated from routes

**Key Modules:**

#### Routers (API Endpoints)
```python
routers/
├── connection.py   # Database connection management
├── metrics.py      # Query metrics endpoints
├── analysis.py     # AI analysis endpoints
├── health.py       # Health check endpoints
└── settings.py     # Configuration endpoints
```

#### Services (Business Logic)
```python
services/
├── metric_service.py       # Fetch metrics from performance_schema
├── schema_service.py       # Table and index information
├── llm_service.py          # AI-powered analysis
└── health_scan_service.py  # Database health checks
```

#### LLM Providers
```python
llm/
├── base.py              # Base LLM provider interface
├── gemini_provider.py   # Google Gemini integration
├── openai_provider.py   # OpenAI GPT integration
└── factory.py           # Provider factory pattern
```

### 3. Data Collection Layer

**MySQL Performance Schema Integration:**

MySQLens collects metrics from MySQL's `performance_schema`:

```sql
-- Query metrics
performance_schema.events_statements_summary_by_digest

-- Connection stats
performance_schema.global_status

-- Index usage
performance_schema.table_io_waits_summary_by_index_usage

-- Table statistics
information_schema.tables
```

**Metrics Collected:**
- Query digest (normalized query fingerprint)
- Execution count
- Total/average/min/max execution time
- Rows examined vs rows sent
- Temporary tables created
- Sort operations
- Lock time

### 4. Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Collect Metrics                                         │
│     ↓                                                       │
│     [performance_schema queries]                            │
│                                                             │
│  2. Extract Context                                         │
│     ↓                                                       │
│     [Table schemas, indexes, row counts]                    │
│                                                             │
│  3. AI Analysis                                             │
│     ↓                                                       │
│     [LLM Provider → Structured Recommendations]             │
│     │                                                       │
│     ├─ Gemini (Primary)                                     │
│     ├─ OpenAI (Fallback)                                    │
│     ├─ DeepSeek (Alternative)                               │
│     └─ Heuristic (No API key)                               │
│                                                             │
│  4. Store Results                                           │
│     ↓                                                       │
│     [SQLite → Recommendations Table]                        │
│                                                             │
│  5. Display to User                                         │
│     ↓                                                       │
│     [Dashboard UI]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. LLM Integration

**Multi-Provider Strategy:**

1. **Primary**: Google Gemini 2.0 Flash
   - Fast and cost-effective
   - Good at structured output
   - JSON mode support

2. **Fallback**: OpenAI GPT-4o
   - High-quality analysis
   - Reliable JSON output
   - More expensive

3. **Alternative**: DeepSeek Chat
   - Open-source friendly
   - Cost-effective
   - Good for specific use cases

4. **Heuristic Fallback**:
   - Used when no API key is configured
   - Rule-based analysis
   - Pattern matching

**LLM Prompt Structure:**
```
System: You are a MySQL database performance expert.

User:
Query: [SQL QUERY]

Schema Context:
- Table: users (1M rows)
  Columns: id, email, name, created_at
  Indexes: PRIMARY (id), idx_email (email)

Metrics:
- Total time: 5000ms
- Calls: 1000
- Rows examined: 1,000,000
- Rows sent: 100

Provide:
1. Analysis of performance issues
2. Index recommendations
3. Query rewrites
4. Risk assessment
```

### 6. Storage Layer

**SQLite for Local Storage:**

```sql
-- Settings table
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);

-- Recommendations table
CREATE TABLE recommendations (
    id TEXT PRIMARY KEY,
    query_digest TEXT,
    recommendation_type TEXT,
    title TEXT,
    description TEXT,
    sql_fix TEXT,
    status TEXT,
    applied INTEGER,
    created_at TIMESTAMP
);

-- Audit log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    action_type TEXT,
    query_digest TEXT,
    details TEXT,
    created_at TIMESTAMP
);
```

## Data Flow

### 1. Connection Flow
```
User → ConnectionForm → POST /api/connection/connect
     → ConnectionManager → aiomysql.create_pool()
     → MySQL Database → Test Query
     → Enable performance_schema consumers
     → Return success
```

### 2. Metrics Flow
```
Dashboard → SWR fetch → GET /api/metrics/queries
         → MetricService → Query performance_schema
         → Parse and format results
         → Return to frontend
         → Display in table
```

### 3. Analysis Flow
```
User clicks "Analyze" → POST /api/analysis/analyze
                     → LLMService.analyze_and_recommend()
                     → SchemaService.get_context()
                     → LLMFactory.create_provider()
                     → Provider.generate_recommendation()
                     → Parse JSON response
                     → Save to SQLite
                     → Return to frontend
                     → Display recommendations
```

## Performance Considerations

### Frontend Optimization
- SWR caching reduces API calls
- Automatic revalidation every 5-10 seconds
- Optimistic UI updates
- Code splitting with Next.js

### Backend Optimization
- AsyncIO for non-blocking I/O
- Connection pooling (2-10 connections)
- Response caching (1 hour TTL)
- Efficient SQL queries

### Database Optimization
- Read-only connections by default
- Indexed queries on performance_schema
- Limited result sets (top 50 queries)
- Efficient aggregations

## Security Architecture

### Privacy Guarantees
1. **Local Processing**: All data stays on localhost
2. **No Upload**: Queries never sent to external services except sanitized prompts to LLM
3. **API Keys**: Stored in environment variables, never exposed
4. **Read-Only**: Default connection mode is read-only

### API Key Management
```
Environment (.env) → Docker Compose → Backend Container → LLM Provider
                                   ↓
                          Never exposed to frontend
```

### Connection Security
- Credentials stored in SQLite (encrypted at rest)
- HTTPS support for production
- CORS configured for localhost only
- No credential logging

## Scalability

### Current Limitations
- Single database connection
- In-memory caching (per container)
- No horizontal scaling

### Future Enhancements
- Multi-database support
- Redis for shared caching
- Background workers for analysis
- Kubernetes deployment

## Error Handling

### Levels of Fallback
1. **Connection Errors**: Graceful reconnection
2. **Query Errors**: Return empty results with error message
3. **LLM Errors**: Fall back to heuristic analysis
4. **API Errors**: Return user-friendly error messages

### Logging Strategy
```
ERROR: Critical failures (connection lost, API errors)
WARN:  Non-critical issues (LLM timeout, cache miss)
INFO:  Normal operations (connection established, analysis complete)
DEBUG: Detailed information (SQL queries, API responses)
```

## Deployment Strategies

### Docker Compose (Default)
```bash
docker compose up -d
```

### Development Mode
```bash
docker compose -f docker compose.dev.yml up
```

### Production Considerations
- Use environment-specific `.env` files
- Enable HTTPS with reverse proxy (nginx)
- Set up log aggregation
- Configure backup for SQLite database
- Use health checks for monitoring

## Testing Strategy

### Backend Tests
- Unit tests for services
- Integration tests for routers
- Mock LLM providers for testing
- Database fixtures

### Frontend Tests
- Component tests with React Testing Library
- E2E tests with Playwright
- Visual regression tests

## Monitoring

### Health Endpoints
- `GET /health` - Overall system health
- `GET /api/health/scan` - Database health check
- `GET /api/connection/status` - Connection status

### Metrics to Monitor
- API response times
- Database query latency
- LLM API success rate
- Error rates
- Connection pool status

---

This architecture is designed to be:
- **Scalable**: Can be extended with additional features
- **Maintainable**: Clear separation of concerns
- **Secure**: Privacy-first approach
- **Reliable**: Fallback mechanisms at every layer
- **Fast**: Async operations and caching

