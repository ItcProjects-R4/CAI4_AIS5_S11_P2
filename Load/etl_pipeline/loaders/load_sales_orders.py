"""Loader for sales orders CSV into `stg_sales_order` table with explicit mapping and validations."""
from pathlib import Path
from ..config import DATA_DIR
from ..db_connection import create_db_engine
from ..logger import get_logger
from .loader_utils import load_csv_to_table


logger = get_logger("load_sales_orders")


STAGING_TABLE = "stg_sales_order"
STAGING_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "order_status",
    "currency",
    "order_total",
    "created_at",
    "updated_at",
    "etl_batch_id",
    "source_system",
    "source_record_id",
]


def run() -> dict:
    engine = create_db_engine()
    csv_file = Path(DATA_DIR) / "sales_orders.csv"
    summary = load_csv_to_table(csv_file, STAGING_TABLE, engine, STAGING_COLUMNS, logger)
    return summary


if __name__ == "__main__":
    res = run()
    print(res)
