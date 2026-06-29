"""
ETL Pipeline Configuration
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Data directories ───────────────────────────────────────────────
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"

# ── Source clean CSVs (read-only ground truth) ─────────────────────
SOURCE_FILES = {
    "etl_batch": CLEAN_DIR / "etl_batch.csv",
    "contacts": CLEAN_DIR / "contacts.csv",
    "customers": CLEAN_DIR / "customers.csv",
    "products": CLEAN_DIR / "products.csv",
    "sales_orders": CLEAN_DIR / "sales_orders.csv",
    "order_lines": CLEAN_DIR / "order_lines.csv",
}

# ── Raw output ─────────────────────────────────────────────────────
RAW_FILES = {
    "etl_batch": RAW_DIR / "etl_batch.csv",
    "contacts": RAW_DIR / "contacts.csv",
    "customers": RAW_DIR / "customers.csv",
    "products": RAW_DIR / "products.csv",
    "sales_orders": RAW_DIR / "sales_orders.csv",
    "order_lines": RAW_DIR / "order_lines.csv",
}

# ── Pipeline output (transform/validate write here) ────────────────
CLEAN_FILES = {
    "etl_batch": CLEAN_DIR / "etl_batch.csv",
    "contacts": CLEAN_DIR / "contacts.csv",
    "customers": CLEAN_DIR / "customers.csv",
    "products": CLEAN_DIR / "products.csv",
    "sales_orders": CLEAN_DIR / "sales_orders.csv",
    "order_lines": CLEAN_DIR / "order_lines.csv",
}

QUARANTINE_FILES = {
    "contacts": QUARANTINE_DIR / "contacts.csv",
    "customers": QUARANTINE_DIR / "customers.csv",
    "products": QUARANTINE_DIR / "products.csv",
    "sales_orders": QUARANTINE_DIR / "sales_orders.csv",
    "order_lines": QUARANTINE_DIR / "order_lines.csv",
}

REJECTED_FILES = {
    "contacts": REJECTED_DIR / "contacts.csv",
    "customers": REJECTED_DIR / "customers.csv",
    "products": REJECTED_DIR / "products.csv",
    "sales_orders": REJECTED_DIR / "sales_orders.csv",
    "order_lines": REJECTED_DIR / "order_lines.csv",
}

# ── ETL internals ──────────────────────────────────────────────────
ETL_DIR = PROJECT_ROOT / "etl"
LOG_DIR = ETL_DIR / "logs"
SQL_SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "sql" / "scripts"

# ── Database settings ──────────────────────────────────────────────
DB_CONFIG = {
    "host": "/var/run/postgresql",
    "port": 5433,
    "database": "crm_db",
    "user": "alih",
    "password": "",
}

_DB_PROMPTED = False


def prompt_db_config() -> dict:
    """Interactively ask user for PostgreSQL connection details."""
    global DB_CONFIG, _DB_PROMPTED
    if _DB_PROMPTED:
        return DB_CONFIG
    _DB_PROMPTED = True

    print("\n╔══════════════════════════════════════════╗")
    print("║  PostgreSQL Connection Configuration     ║")
    print("╚══════════════════════════════════════════╝\n")

    host = input(f"  Host     [{DB_CONFIG['host']}]: ").strip()
    if host:
        DB_CONFIG["host"] = host

    port = input(f"  Port     [{DB_CONFIG['port']}]: ").strip()
    if port:
        try:
            DB_CONFIG["port"] = int(port)
        except ValueError:
            print("  ⚠ Invalid port, using default 5432")

    db = input(f"  Database [{DB_CONFIG['database']}]: ").strip()
    if db:
        DB_CONFIG["database"] = db

    user = input(f"  User     [{DB_CONFIG['user'] or 'postgres'}]: ").strip()
    DB_CONFIG["user"] = user or DB_CONFIG["user"] or "postgres"

    import getpass
    pw = getpass.getpass(f"  Password [***]: ").strip()
    DB_CONFIG["password"] = pw

    print(f"\n  → Connecting to {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}\n")
    return DB_CONFIG

# ── Data quality injection rates ───────────────────────────────────
INJECTION_RATES = {
    "null_rate": 0.03,
    "duplicate_rate": 0.02,
    "invalid_email_rate": 0.02,
    "invalid_phone_rate": 0.02,
    "casing_inconsistency_rate": 0.05,
    "whitespace_issue_rate": 0.04,
    "invalid_date_rate": 0.01,
    "future_date_rate": 0.01,
    "broken_fk_rate": 0.01,
    "calculation_error_rate": 0.02,
    "outlier_rate": 0.01,
    "formatting_inconsistency_rate": 0.03,
}

# ── Load order (FK dependencies) ──────────────────────────────────
LOAD_ORDER = [
    "etl_batch",
    "contacts",
    "customers",
    "products",
    "sales_orders",
    "order_lines",
]

# ── Mapping from config plural names to SQL singular table names ──
STAGING_TABLE_MAP = {
    "etl_batch": "stg_etl_batch",
    "contacts": "stg_contact",
    "customers": "stg_customer",
    "products": "stg_product",
    "sales_orders": "stg_sales_order",
    "order_lines": "stg_order_line",
}

GOLD_TABLE_MAP = {
    "etl_batch": "etl_batch",
    "contacts": "contact",
    "customers": "customer",
    "products": "product",
    "sales_orders": "sales_order",
    "order_lines": "order_line",
}

# ── Business rules ────────────────────────────────────────────────
VALID_ORDER_STATUSES = {
    "pending": ["pending", "pendign", "pneding"],
    "completed": [
        "completed", "cmopleted", "comlpeted", "compleetd",
        "completde", "complteed", "copmleted",
    ],
    "cancelled": ["cancelled"],
    "shipped": ["shipped"],
}

VALID_SEGMENTS = {
    "b2b": ["b2b", "B2B"],
    "b2c": ["b2c", "B2C"],
    "corporate": ["corporate"],
    "retail": ["retail"],
}

VALID_CURRENCIES = {"USD", "EGP"}

VALID_STATUSES = {"active": ["active", "Active"], "inactive": ["inactive"]}

PRODUCT_CATEGORIES_CANONICAL = {
    "northwindcategory": "NorthwindCategory",
    "northwindcategories": "NorthwindCategory",
    "groceries": "Groceries",
    "grcoeries": "Groceries",
    "electronics": "Electronics",
    "food": "Food",
    "clothing": "Clothing",
    "beauty": "Beauty",
    "fragrances": "Fragrances",
    "fargrances": "Fragrances",
    "furniture": "Furniture",
    "kitchen-accessories": "Kitchen-Accessories",
    "home-decoration": "Home-Decoration",
    "sports-accessories": "Sports-Accessories",
    "laptops": "Laptops",
    "womens-jewellery": "Womens-Jewellery",
}

DEPARTMENTS_CANONICAL = {
    "marketing": "Marketing",
    "marekting": "Marketing",
    "accounting": "Accounting",
    "bsuiness development": "Business Development",
    "business development": "Business Development",
    "engineering": "Engineering",
    "human resources": "Human Resources",
    "legal": "Legal",
    "product management": "Product Management",
    "research and development": "Research and Development",
    "sales": "Sales",
    "services": "Services",
    "support": "Support",
    "training": "Training",
}

# ── CSV column definitions ─────────────────────────────────────────
FIELDS = {
    "etl_batch": ["etl_batch_id", "pipeline_run_id", "started_at", "ended_at", "status", "notes"],
    "contacts": ["contact_id", "email", "full_name", "phone", "country",
                 "address_line1", "city", "state", "postal_code",
                 "company_name", "department", "job_title", "attributes_json",
                 "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id"],
    "customers": ["customer_id", "contact_id", "customer_since", "status", "segment",
                  "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id"],
    "products": ["product_id", "sku", "product_name", "category", "brand",
                 "list_price", "is_active", "attributes_json", "created_at", "updated_at",
                 "etl_batch_id", "source_system", "source_record_id"],
    "sales_orders": ["order_id", "customer_id", "order_date", "order_status", "currency",
                     "order_total", "created_at", "updated_at", "etl_batch_id",
                     "source_system", "source_record_id"],
    "order_lines": ["order_line_id", "order_id", "product_id", "line_number", "quantity", "unit_price"],
}

REASON_FIELDS = ["_reject_reason", "_quarantine_reason"]
