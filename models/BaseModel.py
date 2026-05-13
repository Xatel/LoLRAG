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
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 5432))
        self.database = os.getenv("DB_NAME", "lol_rag")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.connection = None
        self.id = None
        for col in self.__class__.columns:
            setattr(self, col, None)

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def connect(self) -> bool:
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
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    @contextmanager
    def cursor(self):
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

    # -------------------------------------------------------------------------
    # Internal DB helpers
    # -------------------------------------------------------------------------

    def _db_query_by_id(self, table: str, id: int) -> dict | None:
        try:
            with self.cursor() as cur:
                cur.execute(f"SELECT * FROM {table} WHERE id = %s", (id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error querying {table}: {e}")
            return None

    def _db_insert(self, table: str, data: dict) -> int | None:
        try:
            with self.cursor() as cur:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                cur.execute(
                    f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id",
                    tuple(data.values())
                )
                new_id = cur.fetchone()["id"]
                logger.info(f"Inserted into {table} with ID: {new_id}")
                return new_id
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}")
            return None

    def _db_update(self, table: str, id: int, data: dict) -> bool:
        try:
            with self.cursor() as cur:
                set_clause = ", ".join(f"{col} = %s" for col in data.keys())
                cur.execute(
                    f"UPDATE {table} SET {set_clause} WHERE id = %s",
                    (*data.values(), id)
                )
                logger.info(f"Updated {table} ID {id}")
                return True
        except Exception as e:
            logger.error(f"Error updating {table} ID {id}: {e}")
            return False

    def _db_delete(self, table: str, id: int) -> bool:
        try:
            with self.cursor() as cur:
                cur.execute(f"DELETE FROM {table} WHERE id = %s", (id,))
                logger.info(f"Deleted from {table} ID {id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting from {table} ID {id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # Public ORM-style methods (operate on self's attributes)
    # -------------------------------------------------------------------------

    def _collect(self) -> dict:
        return {col: getattr(self, col) for col in self.__class__.columns if getattr(self, col) is not None}

    def _populate(self, row: dict) -> None:
        self.id = row.get("id")
        for col in self.__class__.columns:
            if col in row:
                setattr(self, col, row[col])

    def insert(self) -> int | None:
        new_id = self._db_insert(self.table_name, self._collect())
        if new_id is not None:
            self.id = new_id
        return new_id

    def get_by_id(self, id: int) -> bool:
        row = self._db_query_by_id(self.table_name, id)
        if row:
            self._populate(row)
            return True
        return False

    def update(self) -> bool:
        if self.id is None:
            raise ValueError("Cannot update: id is not set.")
        return self._db_update(self.table_name, self.id, self._collect())

    def delete(self) -> bool:
        if self.id is None:
            raise ValueError("Cannot delete: id is not set.")
        return self._db_delete(self.table_name, self.id)

    # -------------------------------------------------------------------------
    # Context manager
    # -------------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
