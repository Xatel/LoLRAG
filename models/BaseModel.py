import logging
from contextlib import asynccontextmanager
from psycopg.rows import dict_row
from dotenv import load_dotenv, find_dotenv
from utils.schema_parser import load_schema
from utils.db_pool import get_pool

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv())


class BaseModel:
    table_name: str = ""
    columns: dict[str, str] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, "table_name", ""):
            cls.columns = load_schema().get(cls.table_name, {})

    def __init__(self):
        self.id = None
        for col in self.__class__.columns:
            setattr(self, col, None)

    def __setattr__(self, name: str, value) -> None:
        if name != "id" and name not in self.__class__.columns:
            valid = list(self.__class__.columns.keys())
            raise AttributeError(
                f"'{name}' is not a valid column for '{self.table_name}'. Valid columns: {valid}"
            )
        super().__setattr__(name, value)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @asynccontextmanager
    async def _cursor(self):
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                yield cur

    def _collect(self) -> dict:
        return {col: getattr(self, col) for col in self.__class__.columns if getattr(self, col) is not None}

    def _populate(self, row: dict) -> None:
        self.id = row.get("id")
        for col in self.__class__.columns:
            if col in row:
                setattr(self, col, row[col])

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    async def insert(self) -> int | None:
        data = self._collect()
        try:
            async with self._cursor() as cur:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                await cur.execute(
                    f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders}) RETURNING id",
                    tuple(data.values())
                )
                row = await cur.fetchone()
                self.id = row["id"]
                logger.info(f"Inserted into {self.table_name} with ID: {self.id}")
                return self.id
        except Exception as e:
            logger.error(f"Error inserting into {self.table_name}: {e}")
            return None

    async def get_by_id(self, id: int) -> bool:
        try:
            async with self._cursor() as cur:
                await cur.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", (id,))
                row = await cur.fetchone()
                if row:
                    self._populate(row)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error querying {self.table_name}: {e}")
            return False

    async def update(self) -> bool:
        if self.id is None:
            raise ValueError("Cannot update: id is not set.")
        data = self._collect()
        try:
            async with self._cursor() as cur:
                set_clause = ", ".join(f"{col} = %s" for col in data.keys())
                await cur.execute(
                    f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s",
                    (*data.values(), self.id)
                )
                logger.info(f"Updated {self.table_name} ID {self.id}")
                return True
        except Exception as e:
            logger.error(f"Error updating {self.table_name} ID {self.id}: {e}")
            return False

    async def delete(self) -> bool:
        if self.id is None:
            raise ValueError("Cannot delete: id is not set.")
        try:
            async with self._cursor() as cur:
                await cur.execute(f"DELETE FROM {self.table_name} WHERE id = %s", (self.id,))
                logger.info(f"Deleted from {self.table_name} ID {self.id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting from {self.table_name} ID {self.id}: {e}")
            return False
