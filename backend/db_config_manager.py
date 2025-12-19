"""
Database Configuration Manager for MySQLens.
Manages saved database connections from db-config.json file.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_CONFIG_FILE = Path(__file__).parent / "db-config.json"


class DBConfigManager:
    """Manages database connection configurations."""
    
    def __init__(self):
        self.config_file = DB_CONFIG_FILE
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Ensure the config file exists."""
        if not self.config_file.exists():
            logger.info(f"Creating default db-config.json at {self.config_file}")
            self._write_config({
                "connections": [],
                "auto_connect": False
            })
    
    def _read_config(self) -> Dict[str, Any]:
        """Read the configuration file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading db-config.json: {e}")
            return {"connections": [], "auto_connect": False}
    
    def _write_config(self, config: Dict[str, Any]):
        """Write to the configuration file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing db-config.json: {e}")
            raise
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all saved connections (without passwords)."""
        config = self._read_config()
        connections = []
        for conn in config.get("connections", []):
            # Return without password for security
            connections.append({
                "name": conn.get("name", "Unnamed"),
                "host": conn.get("host", ""),
                "port": conn.get("port", 3306),
                "user": conn.get("user", ""),
                "database": conn.get("database", ""),
                "is_default": conn.get("is_default", False)
            })
        return connections
    
    def get_connection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific connection by name (with password)."""
        config = self._read_config()
        for conn in config.get("connections", []):
            if conn.get("name") == name:
                return conn
        return None
    
    def get_default_connection(self) -> Optional[Dict[str, Any]]:
        """Get the default connection (with password)."""
        config = self._read_config()
        for conn in config.get("connections", []):
            if conn.get("is_default", False):
                return conn
        return None
    
    def save_connection(self, connection: Dict[str, Any]) -> bool:
        """Save or update a connection."""
        try:
            config = self._read_config()
            connections = config.get("connections", [])
            
            # Find existing connection with same name
            existing_index = None
            for i, conn in enumerate(connections):
                if conn.get("name") == connection.get("name"):
                    existing_index = i
                    break
            
            # If this is set as default, unset others
            if connection.get("is_default", False):
                for conn in connections:
                    conn["is_default"] = False
            
            # Update or add connection
            if existing_index is not None:
                connections[existing_index] = connection
                logger.info(f"Updated connection: {connection.get('name')}")
            else:
                connections.append(connection)
                logger.info(f"Added new connection: {connection.get('name')}")
            
            config["connections"] = connections
            self._write_config(config)
            return True
            
        except Exception as e:
            logger.error(f"Error saving connection: {e}")
            return False
    
    def delete_connection(self, name: str) -> bool:
        """Delete a connection by name."""
        try:
            config = self._read_config()
            connections = config.get("connections", [])
            
            # Filter out the connection
            new_connections = [c for c in connections if c.get("name") != name]
            
            if len(new_connections) == len(connections):
                logger.warning(f"Connection not found: {name}")
                return False
            
            config["connections"] = new_connections
            self._write_config(config)
            logger.info(f"Deleted connection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting connection: {e}")
            return False
    
    def set_auto_connect(self, auto_connect: bool) -> bool:
        """Set whether to auto-connect on startup."""
        try:
            config = self._read_config()
            config["auto_connect"] = auto_connect
            self._write_config(config)
            return True
        except Exception as e:
            logger.error(f"Error setting auto_connect: {e}")
            return False
    
    def get_auto_connect(self) -> bool:
        """Get auto-connect setting."""
        config = self._read_config()
        return config.get("auto_connect", False)


# Global instance
db_config_manager = DBConfigManager()

