     1	# MySQLens API Endpoints
     2	
     3	## Base URL
     4	- Local: `http://localhost:8080`
     5	- Docker: `http://mysqlens-api:8080`
     6	
     7	## Connection Endpoints
     8	
     9	### GET /api/connection/status
    10	Get current connection status.
    11	
    12	**Response:**
    13	```json
    14	{
    15	  "connected": true,
    16	  "host": "mysql-host.example.com",
    17	  "port": 3306,
    18	  "database": "your_database",
    19	  "version": "8.0.x",
    20	  "user": "your_user"
    21	}
    22	```
    23	
    24	### POST /api/connection/connect
    25	Establish connection to MySQL database.
    26	
    27	**Request:**
    28	```json
    29	{
    30	  "host": "mysql-host.example.com",
    31	  "port": 3306,
    32	  "user": "your_user",
    33	  "password": "your_password",
    34	  "database": "your_database"
    35	}
    36	```
    37	
    38	### POST /api/connection/disconnect
    39	Disconnect from MySQL database.
    40	
    41	### POST /api/connection/test
    42	Test connection without saving.
    43	
    44	## Metrics Endpoints
    45	
    46	### GET /api/metrics/vitals
    47	Get database vitals (QPS, buffer pool, connections).
    48	
    49	**Response:**
    50	```json
    51	{
    52	  "success": true,
    53	  "data": {
    54	    "qps": { "value": 296.38, "status": "ok" },
    55	    "buffer_pool_hit_ratio": { "value": 100.0, "status": "ok" },
    56	    "active_connections": { "value": 382, "status": "ok" },
    57	    "max_connections": { "value": 3000, "status": "ok" }
    58	  }
    59	}
    60	```
    61	
    62	### GET /api/metrics/queries?limit=50
    63	Get top slow queries.
    64	
    65	**Query Parameters:**
    66	- `limit` (optional): Number of queries to return (default: 50)
    67	
    68	### GET /api/metrics/db-info
    69	Get database information and statistics.
    70	
    71	### POST /api/metrics/reset
    72	Reset performance schema statistics.
    73	
    74	## Analysis Endpoints
    75	
    76	### GET /api/analysis/indexes/unused?min_size_mb=1.0
    77	Get unused index recommendations.
    78	
    79	**Query Parameters:**
    80	- `min_size_mb` (optional): Minimum index size in MB (default: 1.0)
    81	
    82	### GET /api/analysis/indexes/redundant
    83	Get redundant index recommendations.
    84	
    85	### GET /api/analysis/indexes/missing
    86	Get missing index recommendations.
    87	
    88	### GET /api/analysis/indexes/full
    89	Run full index analysis (unused, redundant, missing).
    90	
    91	### GET /api/analysis/indexes/stats
    92	Get database index statistics.
    93	
    94	## Health Endpoints
    95	
    96	### GET /api/health
    97	Get API health status.
    98	
    99	### GET /api/health/scan
   100	Run comprehensive health scan.
   101	
   102	## Settings Endpoints
   103	
   104	### GET /api/settings/llm-providers
   105	Get available LLM providers.
   106	
   107	**Response:**
   108	```json
   109	{
   110	  "success": true,
   111	  "data": {
   112	    "available": ["openai", "gemini", "deepseek"],
   113	    "current": "gemini"
   114	  }
   115	}
   116	```
   117	
   118	### GET /api/settings/config
   119	Get current configuration (non-sensitive).
   120	
   121	## Documentation
   122	
   123	- Swagger UI: http://localhost:8080/docs
   124	- ReDoc: http://localhost:8080/redoc
   125	
   126	## Notes
   127	
   128	- All endpoints return JSON responses
   129	- Most endpoints require an active database connection
   130	- Error responses follow the format:
   131	  ```json
   132	  {
   133	    "success": false,
   134	    "message": "Error message",
   135	    "error": "Detailed error"
   136	  }
   137	  ```
