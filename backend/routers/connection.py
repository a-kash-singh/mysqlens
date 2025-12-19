"""
Connection management router for MySQLens.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List
from models import ConnectionConfig, ConnectionStatus, APIResponse
from connection_manager import connection_manager
from db_config_manager import db_config_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/test")
async def test_connection(config: ConnectionConfig):
    """Test database connection without establishing permanent connection."""
    try:
        # Attempt connection
        import aiomysql
        conn = await aiomysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            db=config.database
        )
        
        # Test query
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT VERSION() as version")
            result = await cursor.fetchone()
            version = result[0] if result else "Unknown"
        
        conn.close()
        
        return APIResponse(
            success=True,
            message="Connection successful",
            data={"version": version}
        )
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connect")
async def connect_database(config: ConnectionConfig):
    """Establish database connection."""
    try:
        success = await connection_manager.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database
        )
        
        if success:
            conn_info = connection_manager.get_connection_info()
            return APIResponse(
                success=True,
                message="Connected to MySQL",
                data=conn_info
            )
        else:
            raise HTTPException(status_code=500, detail="Connection failed")
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disconnect")
async def disconnect_database():
    """Close database connection."""
    try:
        await connection_manager.disconnect()
        return APIResponse(
            success=True,
            message="Disconnected from MySQL",
            data=None
        )
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status():
    """Get current connection status."""
    conn_info = connection_manager.get_connection_info()
    
    if conn_info:
        return ConnectionStatus(
            connected=True,
            host=conn_info.get("host"),
            port=conn_info.get("port"),
            database=conn_info.get("database"),
            version=conn_info.get("version"),
            user=conn_info.get("user")
        )
    else:
        return ConnectionStatus(
            connected=False,
            host=None,
            port=None,
            database=None,
            version=None,
            user=None
        )


# Saved Connections Management

@router.get("/saved")
async def get_saved_connections():
    """Get all saved database connections (without passwords)."""
    try:
        connections = db_config_manager.get_all_connections()
        return APIResponse(
            success=True,
            message=f"Found {len(connections)} saved connection(s)",
            data={"connections": connections}
        )
    except Exception as e:
        logger.error(f"Error getting saved connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_connection(config: ConnectionConfig, name: str, set_as_default: bool = False):
    """Save a database connection configuration."""
    try:
        connection_data = {
            "name": name,
            "host": config.host,
            "port": config.port,
            "user": config.user,
            "password": config.password,
            "database": config.database,
            "is_default": set_as_default
        }
        
        success = db_config_manager.save_connection(connection_data)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Connection '{name}' saved successfully",
                data=None
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save connection")
            
    except Exception as e:
        logger.error(f"Error saving connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{name}")
async def delete_saved_connection(name: str):
    """Delete a saved connection."""
    try:
        success = db_config_manager.delete_connection(name)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Connection '{name}' deleted successfully",
                data=None
            )
        else:
            raise HTTPException(status_code=404, detail=f"Connection '{name}' not found")
            
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved/{name}")
async def get_saved_connection(name: str):
    """Get a specific saved connection (without password)."""
    try:
        connection = db_config_manager.get_connection(name)
        
        if connection:
            # Remove password before returning
            safe_connection = {
                "name": connection.get("name"),
                "host": connection.get("host"),
                "port": connection.get("port"),
                "user": connection.get("user"),
                "database": connection.get("database"),
                "is_default": connection.get("is_default", False)
            }
            return APIResponse(
                success=True,
                message="Connection retrieved",
                data=safe_connection
            )
        else:
            raise HTTPException(status_code=404, detail=f"Connection '{name}' not found")
            
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect-saved/{name}")
async def connect_saved(name: str):
    """Connect using a saved connection configuration."""
    try:
        connection = db_config_manager.get_connection(name)
        
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection '{name}' not found")
        
        # Create ConnectionConfig from saved data
        config = ConnectionConfig(
            host=connection.get("host"),
            port=connection.get("port"),
            user=connection.get("user"),
            password=connection.get("password"),
            database=connection.get("database")
        )
        
        # Establish connection
        await connection_manager.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database
        )
        
        return APIResponse(
            success=True,
            message=f"Connected to '{name}' successfully",
            data={
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "user": config.user
            }
        )
        
    except Exception as e:
        logger.error(f"Error connecting with saved connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
