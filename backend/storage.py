"""
Storage module for MySQLens.
Handles SQLite database for local storage of recommendations and settings.
"""

import logging
import aiosqlite
from typing import Optional, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "mysqlens.db"


async def init_db():
    """Initialize the SQLite database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Settings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recommendations table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                query_digest TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                sql_fix TEXT,
                status TEXT DEFAULT 'pending',
                applied INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP,
                data JSON
            )
        """)
        
        # Audit log table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                query_digest TEXT,
                recommendation_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        logger.info(f"SQLite database initialized at {DB_PATH}")


async def get_setting(key: str) -> Optional[str]:
    """Get a setting value by key."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_setting(key: str, value: Optional[str]):
    """Set a setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO settings (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
            """,
            (key, value, value)
        )
        await db.commit()


async def save_recommendation(recommendation: dict):
    """Save a recommendation to the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO recommendations 
            (id, query_digest, recommendation_type, title, description, sql_fix, status, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                applied = excluded.applied,
                applied_at = excluded.applied_at,
                data = excluded.data
            """,
            (
                recommendation.get('id'),
                recommendation.get('query_digest'),
                recommendation.get('recommendation_type'),
                recommendation.get('title'),
                recommendation.get('description'),
                recommendation.get('sql_fix'),
                recommendation.get('status', 'pending'),
                json.dumps(recommendation)
            )
        )
        await db.commit()


async def get_recommendations(query_digest: Optional[str] = None):
    """Get recommendations, optionally filtered by query digest."""
    async with aiosqlite.connect(DB_PATH) as db:
        if query_digest:
            cursor = await db.execute(
                "SELECT data FROM recommendations WHERE query_digest = ? ORDER BY created_at DESC",
                (query_digest,)
            )
        else:
            cursor = await db.execute(
                "SELECT data FROM recommendations ORDER BY created_at DESC LIMIT 50"
            )
        
        rows = await cursor.fetchall()
        return [json.loads(row[0]) for row in rows]


async def log_audit(action_type: str, query_digest: Optional[str] = None, 
                    recommendation_id: Optional[str] = None, details: Optional[dict] = None):
    """Log an audit entry."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO audit_log (action_type, query_digest, recommendation_id, details)
            VALUES (?, ?, ?, ?)
            """,
            (action_type, query_digest, recommendation_id, json.dumps(details) if details else None)
        )
        await db.commit()

