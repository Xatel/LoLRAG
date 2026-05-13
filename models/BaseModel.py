import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import os
from dotenv import load_dotenv
from utils.schema_parser import load_schema

logger = logging.getLogger(__name__)
load_dotenv()


class BaseModel:
    table_name: str = ""
    columns: dict[str, str] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, "table_name", ""):
            cls.columns = load_schema().get(cls.table_name, {})

    def __init__(self):
        """
        Initialize database connection.
        Database credentials are read from environment variables.
        """
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 5432))
        self.database = os.getenv("DB_NAME", "lol_rag")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.connection = None
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    @contextmanager
    def cursor(self):
        """Context manager for database cursor."""
        if not self.connection:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        cur = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cur.close()
    
    def query_by_id(self, table: str, id: int) -> dict:
        """Generic query by ID."""
        try:
            with self.cursor() as cur:
                cur.execute(f"SELECT * FROM {table} WHERE id = %s", (id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error querying {table}: {e}")
            return None
    
    def insert(self, table: str, data: dict) -> int:
        """Generic insert method."""
        try:
            with self.cursor() as cur:
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                values = tuple(data.values())
                cur.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id", values)
                new_id = cur.fetchone()["id"]
                logger.info(f"Inserted into {table} with ID: {new_id}")
                return new_id
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}")
            return None
    
    def update(self, table: str, id: int, data: dict) -> bool:
        """Generic update by ID."""
        try:
            with self.cursor() as cur:
                set_clause = ", ".join(f"{col} = %s" for col in data.keys())
                values = (*data.values(), id)
                cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = %s", values)
                logger.info(f"Updated {table} ID {id}")
                return True
        except Exception as e:
            logger.error(f"Error updating {table} ID {id}: {e}")
            return False

    def delete(self, table: str, id: int) -> bool:
        """Generic delete by ID."""
        try:
            with self.cursor() as cur:
                cur.execute(f"DELETE FROM {table} WHERE id = %s", (id,))
                logger.info(f"Deleted from {table} ID {id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting from {table} ID {id}: {e}")
            return False

    def __enter__(self):
        """Support 'with' statement."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support 'with' statement."""
        self.close()