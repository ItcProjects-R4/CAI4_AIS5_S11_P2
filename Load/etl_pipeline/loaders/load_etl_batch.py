"""Loader for ETL batch metadata CSV into `stg_etl_batch` table with explicit mapping and validations."""
from pathlib import Path
from ..config import DATA_DIR
from ..db_connection import create_db_engine
from ..logger import get_logger
from .loader_utils import load_csv_to_table


logger = get_logger("load_etl_batch")


STAGING_TABLE = "stg_etl_batch"
STAGING_COLUMNS = [
    "etl_batch_id",
    "pipeline_run_id",
    "started_at",
    "ended_at",
    "status",
    "notes",
]


def run() -> dict:
    engine = create_db_engine()
    csv_file = Path(DATA_DIR) / "etl_batch.csv"
    summary = load_csv_to_table(csv_file, STAGING_TABLE, engine, STAGING_COLUMNS, logger)
    return summary


if __name__ == "__main__":
    res = run()
    print(res)
