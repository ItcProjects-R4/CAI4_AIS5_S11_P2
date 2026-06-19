"""Loader for contacts CSV into `stg_contact` table with explicit mapping and validations.

This loader performs pre-load checks, explicit column mapping, robust insertion,
and returns a detailed summary dictionary.
"""
from pathlib import Path
from ..config import DATA_DIR
from ..db_connection import create_db_engine
from ..logger import get_logger
from .loader_utils import load_csv_to_table


logger = get_logger("load_contacts")


STAGING_TABLE = "stg_contact"
STAGING_COLUMNS = [
    "contact_id",
    "email",
    "full_name",
    "phone",
    "country",
    "address_line1",
    "city",
    "state",
    "postal_code",
    "company_name",
    "department",
    "job_title",
    "attributes_json",
    "created_at",
    "updated_at",
    "etl_batch_id",
    "source_system",
    "source_record_id",
]


def run() -> dict:
    engine = create_db_engine()
    csv_file = Path(DATA_DIR) / "contacts.csv"
    summary = load_csv_to_table(csv_file, STAGING_TABLE, engine, STAGING_COLUMNS, logger)
    return summary


if __name__ == "__main__":
    res = run()
    print(res)
