"""
Database connection utilities with retry logic and health checks.

Supports both local and Docker-based PostgreSQL deployments.
Provides connection pooling, transactional support, and intelligent retry logic
for handling container startup delays and transient network issues.
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, DatabaseError
from contextlib import contextmanager
from typing import Iterator, Tuple, List
import time
import logging

from .config import (
    SQLALCHEMY_DATABASE_URI, DB_HOST, DB_PORT, DB_NAME,
    RETRY_MAX_ATTEMPTS, RETRY_WAIT_SECONDS
)

logger = logging.getLogger("db_connection")


def create_db_engine(echo: bool = False, pool_size: int = 10, max_overflow: int = 20) -> Engine:
    """Create and return a SQLAlchemy Engine with connection pooling.

    Optimized for both local and Docker PostgreSQL deployments.
    
    Args:
        echo: Whether to echo SQL statements (default False)
        pool_size: Connection pool size (default 10)
        max_overflow: Max overflow connections (default 20)
    
    Returns:
        SQLAlchemy Engine instance
    """
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI,
        echo=echo,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    return engine


def test_connection(engine: Engine, retries: int = RETRY_MAX_ATTEMPTS, wait_seconds: int = RETRY_WAIT_SECONDS) -> Tuple[bool, str]:
    """Test database connectivity with automatic retry logic.
    
    This function implements exponential backoff to handle Docker container
    startup delays. Each retry waits longer than the previous one.
    
    Args:
        engine: SQLAlchemy Engine instance
        retries: Number of retry attempts
        wait_seconds: Base wait time between retries
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.close()
            msg = f"Database connection successful (attempt {attempt})"
            logger.info(msg)
            return True, msg
        
        except (OperationalError, DatabaseError) as exc:
            last_error = exc
            if attempt < retries:
                backoff = wait_seconds * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(
                    f"Connection attempt {attempt}/{retries} failed. "
                    f"Retrying in {backoff}s... Error: {exc}"
                )
                time.sleep(backoff)
            else:
                logger.error(f"All {retries} connection attempts failed")
        
        except Exception as exc:
            logger.exception(f"Unexpected error during connection test: {exc}")
            return False, f"Unexpected error: {exc}"
    
    error_msg = (
        f"Failed to connect to PostgreSQL at {DB_HOST}:{DB_PORT} after {retries} attempts. "
        f"Last error: {last_error}. "
        f"Ensure Docker container is running: `docker compose up -d`"
    )
    return False, error_msg
def verify_database_exists(engine: Engine) -> Tuple[bool, str]:
    """
    Verify that the target PostgreSQL database exists.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT 1 FROM pg_database WHERE datname = :dbname"
                ),
                {"dbname": DB_NAME}
            )

            if result.fetchone():
                msg = f"Database '{DB_NAME}' verified"
                logger.info(msg)
                return True, msg

            msg = f"Database '{DB_NAME}' does not exist"
            logger.error(msg)
            return False, msg

    except Exception as exc:
        logger.exception(f"Failed to verify database: {exc}")
        return False, f"Verification failed: {exc}"
    
def verify_staging_tables(engine: Engine, expected_tables: List[str]) -> Tuple[bool, List[str]]:
    """Verify that all expected staging tables exist.
    
    Args:
        engine: SQLAlchemy Engine instance
        expected_tables: List of table names to verify
    
    Returns:
        Tuple of (success: bool, missing_tables: List[str])
    """
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        missing = [t for t in expected_tables if t not in existing_tables]
        
        if not missing:
            msg = f"All {len(expected_tables)} staging tables verified"
            logger.info(msg)
            return True, []
        else:
            msg = f"Missing staging tables: {missing}"
            logger.error(msg)
            return False, missing
    
    except Exception as exc:
        logger.exception(f"Failed to verify staging tables: {exc}")
        return False, expected_tables


@contextmanager
def get_connection(engine: Engine) -> Iterator:
    """Context manager for transactional database access.
    
    Usage:
        with get_connection(engine) as conn:
            conn.execute(text("INSERT INTO table ..."))
            # Transaction auto-commits on exit, rolls back on exception
    
    Args:
        engine: SQLAlchemy Engine instance
    
    Yields:
        SQLAlchemy Connection with active transaction
    """
    with engine.begin() as connection:
        yield connection

