"""
Base database class for DuckDB operations.

All project-specific database classes should inherit from this base class
to reduce code duplication and ensure consistent behavior.
"""

import duckdb
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any, List


class BaseDatabase(ABC):
    """
    Abstract base class for DuckDB database operations.

    Provides common functionality for:
    - Connection management (connect, close, context manager)
    - Query execution with error handling
    - Basic statistics gathering

    Subclasses must implement:
    - create_schema(): Define project-specific tables
    - load_data() or load_from_csv(): Load project data
    - get_full_data(): Return main dataset
    """

    # Subclasses should override these
    DEFAULT_DB_PATH: Path = None
    CSV_PATH: Path = None
    PROJECT_NAME: str = "Unknown"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to DuckDB file. Defaults to class's DEFAULT_DB_PATH.
        """
        if db_path is None and self.DEFAULT_DB_PATH is None:
            raise ValueError(f"{self.__class__.__name__} must define DEFAULT_DB_PATH or provide db_path")

        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> "BaseDatabase":
        """
        Open database connection.

        Returns:
            Self for method chaining.

        Raises:
            duckdb.Error: If connection fails.
        """
        logger.info(f"Connecting to DuckDB: {self.db_path}")
        try:
            self.conn = duckdb.connect(str(self.db_path))
            return self
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection if open."""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

    def __enter__(self) -> "BaseDatabase":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.

        Args:
            sql: SQL query to execute.

        Returns:
            Query results as pandas DataFrame.

        Raises:
            RuntimeError: If not connected to database.
            duckdb.Error: If query execution fails.
        """
        if self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        try:
            return self.conn.execute(sql).fetchdf()
        except Exception as e:
            logger.error(f"Query failed: {sql[:100]}... - Error: {e}")
            raise

    def execute(self, sql: str) -> None:
        """
        Execute SQL statement without returning results.

        Args:
            sql: SQL statement to execute.

        Raises:
            RuntimeError: If not connected to database.
        """
        if self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        self.conn.execute(sql)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if table exists, False otherwise.
        """
        try:
            result = self.query(f"""
                SELECT COUNT(*) as cnt
                FROM information_schema.tables
                WHERE table_name = '{table_name}'
            """)
            return result['cnt'].iloc[0] > 0
        except Exception:
            return False

    def get_table_row_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Number of rows in the table.
        """
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0

    def get_tables(self) -> List[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names.
        """
        result = self.query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """)
        return result['table_name'].tolist()

    def get_basic_stats(self) -> Dict[str, Any]:
        """
        Get basic database statistics.

        Returns:
            Dictionary with table row counts.
        """
        stats = {"project": self.PROJECT_NAME}
        for table in self.get_tables():
            stats[table] = self.get_table_row_count(table)
        return stats

    # Abstract methods that subclasses must implement
    @abstractmethod
    def create_schema(self) -> None:
        """Create the database schema. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_full_data(self) -> pd.DataFrame:
        """Get the main dataset. Must be implemented by subclasses."""
        pass

    # Optional method - subclasses can override
    def get_stats(self) -> Dict[str, Any]:
        """
        Get project-specific statistics.

        Subclasses should override this for custom stats.
        Default implementation returns basic stats.
        """
        return self.get_basic_stats()


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


def ensure_data_directory(db_path: Path) -> None:
    """
    Ensure the directory for the database file exists.

    Args:
        db_path: Path to the database file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
