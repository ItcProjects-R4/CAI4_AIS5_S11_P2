"""Loader for order lines CSV into `stg_order_line` table with explicit mapping and validations."""
from pathlib import Path
from ..config import DATA_DIR
from ..db_connection import create_db_engine
from ..logger import get_logger
from .loader_utils import load_csv_to_table


logger = get_logger("load_order_lines")


STAGING_TABLE = "stg_order_line"
STAGING_COLUMNS = [
    "order_line_id",
    "order_id",
    "product_id",
    "line_number",
    "quantity",
    "unit_price",
]


def run() -> dict:
    engine = create_db_engine()
    csv_file = Path(DATA_DIR) / "order_lines.csv"
    summary = load_csv_to_table(csv_file, STAGING_TABLE, engine, STAGING_COLUMNS, logger)
    return summary


if __name__ == "__main__":
    res = run()
    print(res)
