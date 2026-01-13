# Database Configuration Guide

MySQLens supports saving database connection configurations so you don't have to enter credentials every time.

## 📁 Configuration File

The database connections are stored in `db-config.json` at the project root.

### ⚠️ Security Note

- **`db-config.json`** is automatically added to `.gitignore` to prevent committing credentials
- This file contains passwords in plaintext on disk (use appropriate file permissions)
- For production, consider using environment variables or secret management tools

## 🚀 Quick Start

### Option 1: Manual Configuration

1. Copy the example file:
```bash
cp db-config.example.json db-config.json
```

2. Edit `db-config.json` with your database credentials:
```json
{
  "connections": [
    {
      "name": "Production MySQL",
      "host": "your-mysql-host.com",
      "port": 3306,
      "user": "cdc_user",
      "password": "your_password_here",
      "database": "mysql",
      "is_default": true
    }
  ],
  "auto_connect": false
}
```

3. Start Docker Compose:
```bash
docker compose up -d
```

The `db-config.json` file is automatically mounted into the backend container.

### Option 2: UI Configuration (Recommended)

1. Start the application:
```bash
docker compose up -d
```

2. Open http://localhost:3000

3. Enter your database credentials in the connection form

4. Click "Save Connection" (button will be added in UI)

5. The connection will be saved to `db-config.json` automatically

## 📊 Configuration Format

```json
{
  "connections": [
    {
      "name": "Connection Name",         // Friendly name for this connection
      "host": "mysql-host.example.com",  // MySQL host (IP or hostname)
      "port": 3306,                      // MySQL port (default: 3306)
      "user": "mysql_user",              // MySQL username
      "password": "secret_password",      // MySQL password (stored plaintext)
      "database": "database_name",       // Default database to connect to
      "is_default": true                 // If true, this connection loads by default
    }
  ],
  "auto_connect": false                  // If true, auto-connects on startup
}
```

### Multiple Connections

You can save multiple connections:

```json
{
  "connections": [
    {
      "name": "Production",
      "host": "prod-mysql.example.com",
      "port": 3306,
      "user": "prod_user",
      "password": "prod_password",
      "database": "prod_db",
      "is_default": true
    },
    {
      "name": "Staging",
      "host": "staging-mysql.example.com",
      "port": 3306,
      "user": "staging_user",
      "password": "staging_password",
      "database": "staging_db",
      "is_default": false
    },
    {
      "name": "Development",
      "host": "localhost",
      "port": 3306,
      "user": "dev_user",
      "password": "dev_password",
      "database": "dev_db",
      "is_default": false
    }
  ],
  "auto_connect": true
}
```

## 🔌 API Endpoints

MySQLens provides API endpoints to manage saved connections:

### Get All Saved Connections
```bash
GET /api/connection/saved
```

Returns all saved connections (without passwords).

### Get Specific Connection
```bash
GET /api/connection/saved/{name}
```

Returns a specific saved connection (without password).

### Save Connection
```bash
POST /api/connection/save?name=MyConnection&set_as_default=true
Content-Type: application/json

{
  "host": "mysql-host.example.com",
  "port": 3306,
  "user": "mysql_user",
  "password": "password",
  "database": "database_name"
}
```

### Delete Connection
```bash
DELETE /api/connection/saved/{name}
```

### Connect Using Saved Connection
```bash
POST /api/connection/connect-saved/{name}
```

Connects to MySQL using a saved connection.

## 🔒 Security Best Practices

### File Permissions

Set restrictive permissions on `db-config.json`:

```bash
# Linux/Mac
chmod 600 db-config.json

# This ensures only the file owner can read/write
```

### Environment Variables (Recommended for Production)

Instead of storing passwords in `db-config.json`, use environment variables:

1. Create connections without passwords in `db-config.json`:
```json
{
  "connections": [
    {
      "name": "Production",
      "host": "${MYSQL_HOST}",
      "port": 3306,
      "user": "${MYSQL_USER}",
      "password": "${MYSQL_PASSWORD}",
      "database": "${MYSQL_DATABASE}",
      "is_default": true
    }
  ]
}
```

2. Set environment variables in `.env`:
```bash
MYSQL_HOST=prod-mysql.example.com
MYSQL_USER=prod_user
MYSQL_PASSWORD=secret_password
MYSQL_DATABASE=prod_db
```

### Docker Secrets (Production)

For production deployments, use Docker secrets:

```yaml
services:
  mysqlens-api:
    secrets:
      - mysql_password
    environment:
      - MYSQL_PASSWORD_FILE=/run/secrets/mysql_password

secrets:
  mysql_password:
    external: true
```

## 🔄 Auto-Connect on Startup

To automatically connect to the default database when the container starts:

1. Set `"auto_connect": true` in `db-config.json`
2. Set `"is_default": true` on your preferred connection
3. Restart the containers:
```bash
docker compose restart
```

The application will automatically connect to the default database on startup.

## 🐳 Docker Configuration

The `docker compose.yml` automatically mounts `db-config.json`:

```yaml
volumes:
  - ./backend:/app
  - api_cache:/app/cache
  - ./db-config.json:/app/db-config.json  # ← Config file mounted here
```

Changes to `db-config.json` are immediately available to the container (no rebuild needed).

## 📝 Example Configurations

### Remote RDS Connection
```json
{
  "connections": [
    {
      "name": "AWS RDS Production",
      "host": "my-db.abc123.us-east-1.rds.amazonaws.com",
      "port": 3306,
      "user": "admin",
      "password": "my_rds_password",
      "database": "production",
      "is_default": true
    }
  ],
  "auto_connect": false
}
```

### Local Development
```json
{
  "connections": [
    {
      "name": "Local MySQL",
      "host": "host.docker.internal",
      "port": 3306,
      "user": "root",
      "password": "root",
      "database": "test",
      "is_default": true
    }
  ],
  "auto_connect": true
}
```

### CDC User (Binlog Access)
```json
{
  "connections": [
    {
      "name": "CDC User Connection",
      "host": "mysql-host.example.com",
      "port": 3306,
      "user": "cdc_user",
      "password": "cdc_password",
      "database": "mysql",
      "is_default": true
    }
  ],
  "auto_connect": false
}
```

## 🔧 Troubleshooting

### Connection Saved But Not Loading

1. Check file permissions:
```bash
ls -la db-config.json
```

2. Check JSON syntax:
```bash
cat db-config.json | jq .
```

3. Check Docker logs:
```bash
docker compose logs -f mysqlens-api
```

### File Not Found Error

Make sure `db-config.json` exists in the project root:
```bash
ls -la db-config.json
```

If missing, create from example:
```bash
cp db-config.example.json db-config.json
```

### Passwords Not Working

- Ensure special characters in passwords are properly escaped in JSON
- Use double quotes, not single quotes
- Escape backslashes: `"my\\password"`
- Escape double quotes: `"my\"password"`

## 🎯 Next Steps

1. **Start simple**: Save one connection and test it
2. **Add multiple environments**: Production, staging, development
3. **Enable auto-connect**: For frequently used connections
4. **Secure the file**: Set proper file permissions
5. **Regular backups**: Keep backup of `db-config.json` (without committing to git)

---

## 📞 Support

If you have issues with database configuration:

- Check the [README](./README.md) for general setup
- Review [DEPLOYMENT](./DEPLOYMENT.md) for production tips
- Open an issue: https://github.com/a-kash-singh/mysqlens/issues

---

<div align="center">

**Built with 🔍 for better MySQL performance**

[← Back to README](./README.md)

</div>

