import re
import os

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "postgres-pgvector", "schema.sql")
_schema_cache: dict[str, dict[str, str]] | None = None


def load_schema() -> dict[str, dict[str, str]]:
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache

    with open(_SCHEMA_PATH, "r") as f:
        sql = f.read()

    tables: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"CREATE TABLE \w+\.?(\w+)\s*\((.*?)\);", sql, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1)
        columns: dict[str, str] = {}
        for line in match.group(2).splitlines():
            line = line.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            upper = line.upper()
            if any(upper.startswith(kw) for kw in ("PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT")):
                continue
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0]
                type_def = re.sub(r"--.*$", "", " ".join(parts[1:])).strip()
                columns[col_name] = type_def
        tables[table_name] = columns

    _schema_cache = tables
    return _schema_cache
