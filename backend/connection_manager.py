"""
MySQL connection manager for MySQLens.
Handles connection pooling, health checks, and version detection.
"""

import logging
import aiomysql
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import json
import os

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages MySQL database connections with encryption and pooling."""
    
    def __init__(self):
        self._pool: Optional[aiomysql.Pool] = None
        self._connection_config: Optional[Dict[str, Any]] = None
        self._mysql_version: Optional[str] = None
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for storing credentials."""
        key_file = ".encryption_key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt database credentials."""
        json_data = json.dumps(credentials)
        encrypted = self._cipher.encrypt(json_data.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt database credentials."""
        decrypted = self._cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())
    
    async def connect(
        self,
        host: str,
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "mysql",
        ssl: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Establish connection to MySQL database.
        
        Args:
            host: Database host
            port: Database port (default: 3306)
            user: Database user
            password: Database password
            database: Database name
            ssl: SSL configuration dict
            **kwargs: Additional connection parameters
            
        Returns:
            bool: True if connection successful
        """
        try:
            # Close existing connection if any
            await self.disconnect()
            
            # Store connection config
            self._connection_config = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "db": database,
                "autocommit": True,
                "charset": "utf8mb4",
                **kwargs
            }
            
            # Create connection pool
            self._pool = await aiomysql.create_pool(
                minsize=1,
                maxsize=10,
                **self._connection_config
            )
            
            # Test connection and get version
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT VERSION()")
                    result = await cursor.fetchone()
                    self._mysql_version = result[0] if result else None
                    logger.info(f"Connected to MySQL {self._mysql_version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            self._pool = None
            self._connection_config = None
            raise
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            self._connection_config = None
            self._mysql_version = None
            logger.info("Disconnected from MySQL")
    
    async def get_pool(self) -> Optional[aiomysql.Pool]:
        """Get the current connection pool."""
        return self._pool
    
    async def check_connection_health(self) -> bool:
        """Check if database connection is healthy."""
        if not self._pool:
            return False
        
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result == (1,)
        except Exception as e:
            logger.error(f"Connection health check failed: {e}")
            return False
    
    def get_mysql_version(self) -> Optional[str]:
        """Get MySQL version string."""
        return self._mysql_version
    
    def get_mysql_version_number(self) -> Optional[int]:
        """Get MySQL version as number (e.g., 80032 for 8.0.32)."""
        if not self._mysql_version:
            return None
        
        try:
            # Parse version like "8.0.32" or "5.7.40-log"
            version_parts = self._mysql_version.split("-")[0].split(".")
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) if len(version_parts) > 2 else 0
            return major * 10000 + minor * 100 + patch
        except Exception:
            return None
    
    def is_connected(self) -> bool:
        """Check if connection pool exists."""
        return self._pool is not None
    
    def get_connection_info(self) -> Optional[Dict[str, Any]]:
        """Get current connection information (without password)."""
        if not self._connection_config:
            return None
        
        return {
            "host": self._connection_config.get("host"),
            "port": self._connection_config.get("port"),
            "user": self._connection_config.get("user"),
            "database": self._connection_config.get("db"),
            "version": self._mysql_version,
            "connected": self.is_connected()
        }


# Global connection manager instance
connection_manager = ConnectionManager()
