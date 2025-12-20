"""
Database connection and management.
"""
import psycopg2
from psycopg2 import pool
from flask import g, current_app
from contextlib import contextmanager
import threading

# Thread-safe connection pool
_connection_pool = None
_lock = threading.Lock()

def init_db(app):
    """Initialize database connection pool"""
    global _connection_pool
    
    with _lock:
        if _connection_pool is None:
            try:
                _connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1,  # Minimum connections
                    10,  # Maximum connections
                    dbname=app.config['DB_NAME'],
                    user=app.config['DB_USER'],
                    password=app.config['DB_PASSWORD'],
                    host=app.config['DB_HOST'],
                    port=app.config['DB_PORT']
                )
                # Initialize database schema
                _initialize_schema()
                app.logger.info("✅ Database connection pool created successfully")
            except Exception as e:
                app.logger.error(f"❌ Database connection failed: {e}")
                raise


def _initialize_schema():
    """Initialize database schema (add columns if they don't exist)"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Add favorite column if it doesn't exist
        cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE")
        
        conn.commit()
        cur.close()
    except Exception as e:
        if conn:
            conn.rollback()
        # Ignore error if column already exists
        pass
    finally:
        if conn:
            return_connection(conn)


def get_connection():
    """Get a database connection from the pool"""
    if _connection_pool is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _connection_pool.getconn()


def return_connection(conn):
    """Return a connection to the pool"""
    if _connection_pool:
        _connection_pool.putconn(conn)


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_connection()
    try:
        yield conn
        # Only commit if no exception occurred
        try:
            conn.commit()
        except Exception as commit_error:
            conn.rollback()
            raise commit_error
    except Exception:
        conn.rollback()
        raise
    finally:
        return_connection(conn)


def get_db_connection():
    """Get database connection (for compatibility)"""
    # For request-scoped usage
    if 'db_conn' not in g:
        g.db_conn = get_connection()
        g.db_cur = g.db_conn.cursor()
    return g.db_conn, g.db_cur


def close_db(error=None):
    """Close database connection at end of request"""
    conn = g.pop('db_conn', None)
    if conn is not None:
        return_connection(conn)


def close_pool():
    """Close all connections in the pool"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
