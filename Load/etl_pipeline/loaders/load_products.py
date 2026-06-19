"""Loader for products CSV into `stg_product` table with explicit mapping and validations."""
from pathlib import Path
from ..config import DATA_DIR
from ..db_connection import create_db_engine
from ..logger import get_logger
from .loader_utils import load_csv_to_table


logger = get_logger("load_products")


STAGING_TABLE = "stg_product"
STAGING_COLUMNS = [
    "product_id",
    "sku",
    "product_name",
    "category",
    "brand",
    "list_price",
    "is_active",
    "attributes_json",
    "created_at",
    "updated_at",
    "etl_batch_id",
    "source_system",
    "source_record_id",
]


def run() -> dict:
    engine = create_db_engine()
    csv_file = Path(DATA_DIR) / "products.csv"
    summary = load_csv_to_table(csv_file, STAGING_TABLE, engine, STAGING_COLUMNS, logger)
    return summary


if __name__ == "__main__":
    res = run()
    print(res)
