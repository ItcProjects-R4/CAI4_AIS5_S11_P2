"""
Configuration for the ETL project.

Loads configuration from .env file using python-dotenv.
Supports both local and Docker-based PostgreSQL deployments.

.env file should contain:
- DB_USER: PostgreSQL username (default postgres)
- DB_PASSWORD: PostgreSQL password
- DB_HOST: PostgreSQL hostname or IP (e.g., localhost or postgres container name)
- DB_PORT: PostgreSQL port (default 5432)
- DB_NAME: Database name (default shoporder)
- DB_DRIVER: SQLAlchemy driver (default psycopg2)
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Project directories
BASE_DIR = PROJECT_ROOT
DATA_DIR = BASE_DIR / "cleaned_data"
LOGS_DIR = BASE_DIR / "etl_pipeline" / "execution_logs"
REPORTS_DIR = BASE_DIR / "reports"
DIAGRAMS_DIR = BASE_DIR / "etl_pipeline" / "architecture"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "shoporder")

DB_CONFIG = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "port": DB_PORT,
    "database": DB_NAME,
}

# SQLAlchemy connection configuration
SQLALCHEMY_DRIVER = os.getenv("DB_DRIVER", "psycopg2")
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+{SQLALCHEMY_DRIVER}://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Connection retry settings
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", 3))
RETRY_WAIT_SECONDS = int(os.getenv("RETRY_WAIT_SECONDS", 5))

# ETL configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Business key mapping used by validation to detect duplicates
BUSINESS_KEYS = {
    "stg_etl_batch": ["etl_batch_id"],
    "stg_contact": ["contact_id"],
    "stg_customer": ["customer_id"],
    "stg_product": ["product_id"],
    "stg_sales_order": ["order_id"],
    "stg_order_line": ["order_line_id"],
}

# Staging tables and their expected columns
STAGING_TABLES = {
    "stg_etl_batch": ["etl_batch_id", "pipeline_run_id", "started_at", "ended_at", "status", "notes"],
    "stg_contact": [
        "contact_id", "email", "full_name", "phone", "country",
        "address_line1", "city", "state", "postal_code",
        "company_name", "department", "job_title",
        "attributes_json", "created_at", "updated_at",
        "etl_batch_id", "source_system", "source_record_id"
    ],
    "stg_customer": [
        "customer_id", "contact_id", "customer_since", "status", "segment",
        "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id"
    ],
    "stg_product": [
        "product_id", "sku", "product_name", "category", "brand",
        "list_price", "is_active", "attributes_json",
        "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id"
    ],
    "stg_sales_order": [
        "order_id", "customer_id", "order_date", "order_status", "currency", "order_total",
        "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id"
    ],
    "stg_order_line": [
        "order_line_id", "order_id", "product_id",
        "line_number", "quantity", "unit_price"
    ],
}
