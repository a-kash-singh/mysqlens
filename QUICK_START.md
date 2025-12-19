# 🚀 Quick Start Guide

## Your Database Setup (As Shown in UI):

```
Host: your-mysql-host.com
Port: 3306
User: cdc_user
Database: mysql
```

## Option 1: Quick Connect via Config File (Fastest) ⚡

```bash
# 1. Add your connection
cat > /Users/akashsingh/Downloads/MySQLens/db-config.json << 'EOF'
{
  "connections": [
    {
      "name": "Production",
      "host": "your-mysql-host.com",
      "port": 3306,
      "user": "cdc_user",
      "password": "YOUR_PASSWORD_HERE",
      "database": "mysql",
      "is_default": true
    }
  ],
  "auto_connect": true
}
EOF

# 2. Restart backend
cd /Users/akashsingh/Downloads/MySQLens
docker-compose restart mysqlens-api

# 3. Open dashboard
open http://localhost:3000

# Done! It will auto-connect on startup
```

## Option 2: Connect via UI (Current Method) 🖱️

1. Go to http://localhost:3000
2. Fill in the form:
   - Host: `your-mysql-host.com`
   - Port: `3306`
   - User: `cdc_user`
   - Password: (your password)
   - Database: `mysql`
3. Click "Connect to MySQL"
4. ✅ Dashboard loads with metrics!

## Option 3: Connect via API 🔌

```bash
# Connect
curl -X POST http://localhost:8080/api/connection/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "your-mysql-host.com",
    "port": 3306,
    "user": "cdc_user",
    "password": "YOUR_PASSWORD",
    "database": "mysql"
  }'

# Check status
curl http://localhost:8080/api/connection/status

# Get metrics
curl http://localhost:8080/api/metrics/vitals
curl http://localhost:8080/api/metrics/queries
```

## 📊 What You'll See After Connecting:

- **QPS**: Queries per second (296.38 in your case)
- **Buffer Pool**: Hit ratio percentage (100%)
- **Connections**: Active vs Max (382/3000)
- **Top Slow Queries**: With execution times
- **Index Analysis**: Unused, redundant, missing indexes

## 🔧 Useful Commands:

```bash
# View logs
docker-compose logs -f mysqlens-api

# Restart containers
docker-compose restart

# Stop everything
docker-compose down

# Start everything
docker-compose up -d

# Check status
docker-compose ps
```

## 💡 Pro Tips:

### 1. Save Multiple Connections:

```json
{
  "connections": [
    {
      "name": "Production",
      "host": "your-mysql-host.com",
      "port": 3306,
      "user": "cdc_user",
      "password": "prod_password",
      "database": "mysql",
      "is_default": true
    },
    {
      "name": "Staging",
      "host": "staging.example.com",
      "port": 3306,
      "user": "staging_user",
      "password": "staging_password",
      "database": "staging_db",
      "is_default": false
    }
  ],
  "auto_connect": true
}
```

Then switch connections via API:
```bash
curl -X POST http://localhost:8080/api/connection/connect-saved/Staging
```

### 2. Auto-Connect on Startup:

Set `"auto_connect": true` in `db-config.json` to automatically connect when containers start.

### 3. Hot Reload:

Changes to backend Python code are automatically reloaded (no rebuild needed).

### 4. Security:

```bash
# Set restrictive permissions
chmod 600 db-config.json

# Never commit this file (already in .gitignore)
```

## 🐛 Troubleshooting:

### Connection Refused?
```bash
# Check if MySQL allows remote connections
# In MySQL config (my.cnf):
bind-address = 0.0.0.0  # Not 127.0.0.1

# Firewall:
sudo ufw allow 3306
```

### Permission Denied?
```sql
-- Grant required permissions
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'cdc_user'@'%';
GRANT SELECT ON performance_schema.* TO 'cdc_user'@'%';
GRANT SELECT ON information_schema.* TO 'cdc_user'@'%';
GRANT SELECT ON mysql.* TO 'cdc_user'@'%';
FLUSH PRIVILEGES;
```

### Container Not Starting?
```bash
# Check logs
docker-compose logs mysqlens-api

# Rebuild
docker-compose up -d --build
```

## 📖 More Help:

- Full docs: [README.md](./README.md)
- DB config: [DB_CONFIG_GUIDE.md](./DB_CONFIG_GUIDE.md)
- All changes: [CHANGES_SUMMARY.md](./CHANGES_SUMMARY.md)
- API reference: [API_ENDPOINTS.md](./API_ENDPOINTS.md)

## ✅ Checklist:

- [ ] MySQLens containers running
- [ ] MySQL `performance_schema` enabled
- [ ] User has required permissions
- [ ] Firewall allows port 3306
- [ ] Connection successful in UI
- [ ] Dashboard showing metrics
- [ ] (Optional) Saved connections in `db-config.json`
- [ ] (Optional) Auto-connect enabled

---

**Need help?** Check the logs:
```bash
docker-compose logs -f
```

**Ready to publish?** See [GITHUB_SETUP.md](./GITHUB_SETUP.md)

---

<div align="center">

**Happy Optimizing! 🔍**

</div>

