# MySQLens Scripts

This directory contains utility scripts for testing, benchmarking, and development of MySQLens.

## Directory Structure

```
scripts/
├── README.md                           # This file
├── run_benchmarks.py                   # LLM benchmarking suite
├── test_complete_optimization_flow.py  # End-to-end testing
├── load/
│   ├── generate_load.py               # Continuous load generator
│   └── generate_slow_queries.py       # One-time slow query generator
└── seed/
    ├── init.sql                        # MySQLens schema initialization
    ├── seed_data.py                    # Basic demo data seeder
    ├── seed_complex.py                 # Complex demo data with bottlenecks
    └── seed_golden.sql                 # Golden dataset for LLM validation
```

## Prerequisites

```bash
# Install Python dependencies
pip install aiomysql requests

# Set environment variables
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=yourpassword
export MYSQL_DATABASE=mysqlens_demo
```

## Seed Scripts

### Basic Demo Data (`seed/seed_data.py`)

Creates a demo database with realistic data and intentional performance bottlenecks:

- 1,000 users
- 500 products
- 5,000 orders with order items
- 50,000 log entries
- Intentional missing indexes for demo

```bash
# Run from project root
python scripts/seed/seed_data.py
```

### Complex Demo Data (`seed/seed_complex.py`)

Creates a larger dataset with sophisticated bottlenecks:

- 2,000 users
- 1,000 products with inventory
- 10,000 orders with coupons
- 5,000 reviews
- 100,000 activity logs
- Index bloat, missing indexes, JSON queries

```bash
python scripts/seed/seed_complex.py
```

### Golden Dataset (`seed/seed_golden.sql`)

Creates test tables for LLM benchmark validation:

```bash
mysql -u root -p < scripts/seed/seed_golden.sql
```

### Schema Initialization (`seed/init.sql`)

Creates the MySQLens internal schema for storing results:

```bash
mysql -u root -p < scripts/seed/init.sql
```

## Load Testing

### Continuous Load Generator (`load/generate_load.py`)

Runs in the background generating realistic slow queries:

```bash
# Start load generator (Ctrl+C to stop)
python scripts/load/generate_load.py
```

### Slow Query Generator (`load/generate_slow_queries.py`)

One-time script to generate slow queries for testing:

```bash
python scripts/load/generate_slow_queries.py
```

## Benchmarking & Testing

### LLM Benchmarks (`run_benchmarks.py`)

Runs the golden dataset scenarios against the AI analysis endpoint:

```bash
# Make sure the backend is running first
docker-compose up -d mysqlens-api

# Run benchmarks
python scripts/run_benchmarks.py
```

Output includes:
- Pass/fail status for each scenario
- Response times
- JSON report file with full details

### End-to-End Tests (`test_complete_optimization_flow.py`)

Tests the complete MySQLens flow:

1. API health check
2. Database connection
3. Query metrics retrieval
4. Schema information
5. AI analysis
6. Index recommendations
7. Health scan

```bash
# Make sure services are running
docker-compose up -d

# Seed demo data
python scripts/seed/seed_data.py

# Run E2E tests
python scripts/test_complete_optimization_flow.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `localhost` | MySQL server host |
| `MYSQL_PORT` | `3306` | MySQL server port |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | (empty) | MySQL password |
| `MYSQL_DATABASE` | `mysqlens_demo` | Target database |
| `API_URL` | `http://localhost:8080` | MySQLens API URL |

## Using with Docker

If MySQL is running in Docker:

```bash
# Connect to MySQL in Docker
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306

# Or run scripts inside Docker network
docker-compose exec mysqlens-api python /scripts/seed/seed_data.py
```

## Makefile Commands

From the project root, you can use these commands:

```bash
make seed          # Seed demo data
make seed-complex  # Seed complex demo data
make benchmarks    # Run LLM benchmarks
make e2e-test      # Run end-to-end tests
make load          # Start load generator
```

## Troubleshooting

### Connection Issues

```bash
# Check MySQL is running
mysqladmin ping -h $MYSQL_HOST -u $MYSQL_USER -p

# Check from Docker
docker-compose exec mysqlens-api python -c "import aiomysql; print('OK')"
```

### Performance Schema Not Enabled

The load generator relies on performance_schema. Enable it:

```sql
-- Check if enabled
SHOW VARIABLES LIKE 'performance_schema';

-- In my.cnf
[mysqld]
performance_schema=ON
```

### LLM Provider Issues

If benchmarks timeout, check LLM configuration:

```bash
# Test Ollama
curl http://localhost:11434/api/generate -d '{"model":"llama3.2:latest","prompt":"test"}'

# Or use cloud provider
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key
```
