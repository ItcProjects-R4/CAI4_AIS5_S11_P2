"""
Phase 2 - Silver Transformation Pipeline
=========================================
Reads Bronze Simulated Messy JSON  ->  cleans / validates  ->  writes:
    data/clean/<entity>.csv        (ready for Gold / SQL load)
    data/quarantine/<entity>.csv   (recoverable issues, held for review)
    data/rejected/<entity>.csv     (unrecoverable, dropped from pipeline)

Column names in every output CSV match the MySQL schema exactly.
"""

import os, sys, glob, json, uuid, re, datetime, argparse
import pandas as pd
from dateutil import parser as dateparser

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NAMESPACE_ETL = uuid.uuid5(uuid.NAMESPACE_OID, "shopOrder_etl")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def deterministic_uuid(seed: str) -> str:
    """Return a repeatable UUID‑5 string for a given seed."""
    if pd.isna(seed) or not str(seed).strip():
        return None
    return str(uuid.uuid5(NAMESPACE_ETL, str(seed).strip()))


def derive_source_system(source_id: str) -> str:
    """Derive source_system from the prefix of source_*_id."""
    if pd.isna(source_id) or not source_id:
        return None
    s = str(source_id).strip()
    if s.startswith("nw_"):
        return "northwind"
    if s.startswith("dj_"):
        return "dummyjson"
    return "unknown"


def strip_or_none(val):
    """Strip whitespace; return None for empty / NaN."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def parse_date_safe(raw) -> str | None:
    """
    Parse many date formats -> 'YYYY-MM-DD HH:MM:SS' or None.
    Handles: ISO, dd/mm/yyyy, Excel serial, partial timestamps, etc.
    """
    if pd.isna(raw) or raw == "" or raw is None:
        return None
    raw = str(raw).strip()

    # Excel serial date (pure digits, > 30 000 ≈ 1982+)
    if raw.isdigit() and int(raw) > 30000:
        try:
            dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(int(raw), unit="D")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    # Try dateutil fuzzy parse
    try:
        dt = dateparser.parse(raw, fuzzy=True, dayfirst=True)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_date_to_date(raw) -> str | None:
    """Same as parse_date_safe but returns just YYYY-MM-DD (DATE type)."""
    ts = parse_date_safe(raw)
    if ts is None:
        return None
    return ts[:10]  # first 10 chars = YYYY-MM-DD


def clean_numeric(val):
    """Parse numeric values: strip currency symbols, Arabic decimals, commas."""
    if pd.isna(val) or val == "" or val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val)
    # Arabic decimal separator ٫  ->  .
    s = s.replace("٫", ".").replace(",", ".")
    # Strip everything except digits, minus, dot
    s = re.sub(r"[^\d.\-]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_entity(base_dir: str, entity: str) -> pd.DataFrame:
    """Glob all part‑*.json under base_dir/<entity>/ and return a DataFrame."""
    pattern = os.path.join(base_dir, entity, "**", "*.json")
    files = glob.glob(pattern, recursive=True)
    rows = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            rows.extend(json.load(f))
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ---------------------------------------------------------------------------
# Per‑entity transformers
# ---------------------------------------------------------------------------

def transform_contacts(df: pd.DataFrame, batch_id: str, now: str):
    """
    Schema target: contact table
    Required NOT NULL: contact_id, email, created_at, etl_batch_id
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # --- map columns ---
    out = pd.DataFrame()
    out["contact_id"]       = df["source_contact_id"].apply(deterministic_uuid)
    out["email"]            = df.get("email", pd.Series(dtype=str)).apply(strip_or_none)
    out["full_name"]        = df.get("full_name", pd.Series(dtype=str)).apply(strip_or_none)
    out["phone"]            = df.get("phone", pd.Series(dtype=str)).apply(strip_or_none)
    out["country"]          = df.get("country", pd.Series(dtype=str)).apply(strip_or_none)
    out["address_line1"]    = df.get("address_line1", pd.Series(dtype=str)).apply(strip_or_none)
    out["city"]             = df.get("city", pd.Series(dtype=str)).apply(strip_or_none)
    out["state"]            = df.get("state", pd.Series(dtype=str)).apply(strip_or_none)
    out["postal_code"]      = df.get("postal_code", pd.Series(dtype=str)).apply(strip_or_none)
    out["company_name"]     = df.get("company_name", pd.Series(dtype=str)).apply(strip_or_none)
    out["department"]       = df.get("department", pd.Series(dtype=str)).apply(strip_or_none)
    out["job_title"]        = df.get("job_title", pd.Series(dtype=str)).apply(strip_or_none)
    out["attributes_json"]  = None
    out["created_at"]       = now
    out["updated_at"]       = None
    out["etl_batch_id"]     = batch_id
    out["source_system"]    = df["source_contact_id"].apply(derive_source_system)
    out["source_record_id"] = df["source_contact_id"].apply(strip_or_none)

    # keep DQ columns for routing
    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    # --- rejection: missing contact_id OR missing email ---
    is_rejected = out["contact_id"].isna() | out["email"].isna()

    # --- quarantine: has identity but medium / high severity ---
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    # --- dedup: keep first occurrence per email (fewest nulls first) ---
    out["_nulls"] = out.isnull().sum(axis=1)
    out = out.sort_values(["email", "_nulls"])
    out = out.drop_duplicates(subset=["email"], keep="first")
    # recalculate masks after dedup
    is_rejected   = out["contact_id"].isna() | out["email"].isna()
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    schema_cols = [
        "contact_id", "email", "full_name", "phone", "country",
        "address_line1", "city", "state", "postal_code",
        "company_name", "department", "job_title",
        "attributes_json", "created_at", "updated_at",
        "etl_batch_id", "source_system", "source_record_id",
    ]

    clean  = out.loc[~is_rejected & ~is_quarantine, schema_cols]
    quar   = out.loc[is_quarantine, schema_cols]
    reject = out.loc[is_rejected, schema_cols]
    return clean, quar, reject


def transform_customers(df: pd.DataFrame, batch_id: str, now: str):
    """
    Schema target: customer table
    Required NOT NULL: customer_id, contact_id, created_at, etl_batch_id
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    out = pd.DataFrame()
    out["customer_id"]      = df["source_customer_id"].apply(deterministic_uuid)
    out["contact_id"]       = df["source_contact_id"].apply(deterministic_uuid)
    out["customer_since"]   = df.get("customer_since", pd.Series(dtype=str)).apply(parse_date_to_date)
    out["status"]           = df.get("status", pd.Series(dtype=str)).apply(strip_or_none)
    out["segment"]          = df.get("segment", pd.Series(dtype=str)).apply(strip_or_none)
    out["created_at"]       = now
    out["updated_at"]       = None
    out["etl_batch_id"]     = batch_id
    out["source_system"]    = df["source_customer_id"].apply(derive_source_system)
    out["source_record_id"] = df["source_customer_id"].apply(strip_or_none)

    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    is_rejected   = out["customer_id"].isna() | out["contact_id"].isna()
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    out = out.drop_duplicates(subset=["customer_id"], keep="first")
    is_rejected   = out["customer_id"].isna() | out["contact_id"].isna()
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    schema_cols = [
        "customer_id", "contact_id", "customer_since", "status", "segment",
        "created_at", "updated_at", "etl_batch_id", "source_system", "source_record_id",
    ]

    clean  = out.loc[~is_rejected & ~is_quarantine, schema_cols]
    quar   = out.loc[is_quarantine, schema_cols]
    reject = out.loc[is_rejected, schema_cols]
    return clean, quar, reject


def transform_products(df: pd.DataFrame, batch_id: str, now: str):
    """
    Schema target: product table
    Required NOT NULL: product_id, sku, product_name, is_active, created_at, etl_batch_id
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    out = pd.DataFrame()
    out["product_id"]       = df["source_product_id"].apply(deterministic_uuid)
    out["sku"]              = df.get("sku", pd.Series(dtype=str)).apply(strip_or_none)
    out["product_name"]     = df.get("product_name", pd.Series(dtype=str)).apply(strip_or_none)
    out["category"]         = df.get("category", pd.Series(dtype=str)).apply(strip_or_none)
    out["brand"]            = df.get("brand", pd.Series(dtype=str)).apply(strip_or_none)
    out["list_price"]       = df.get("list_price", pd.Series(dtype=object)).apply(clean_numeric)
    out["is_active"]        = df.get("is_active", pd.Series(dtype=object)).apply(
        lambda v: 1 if v is True or v == 1 else (0 if v is False or v == 0 else 1)
    )
    out["attributes_json"]  = None
    out["created_at"]       = now
    out["updated_at"]       = None
    out["etl_batch_id"]     = batch_id
    out["source_system"]    = df["source_product_id"].apply(derive_source_system)
    out["source_record_id"] = df["source_product_id"].apply(strip_or_none)

    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    is_rejected = (
        out["product_id"].isna()
        | out["sku"].isna()
        | out["product_name"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    out = out.drop_duplicates(subset=["sku"], keep="first")
    is_rejected = (
        out["product_id"].isna()
        | out["sku"].isna()
        | out["product_name"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    schema_cols = [
        "product_id", "sku", "product_name", "category", "brand",
        "list_price", "is_active",
        "attributes_json", "created_at", "updated_at",
        "etl_batch_id", "source_system", "source_record_id",
    ]

    clean  = out.loc[~is_rejected & ~is_quarantine, schema_cols]
    quar   = out.loc[is_quarantine, schema_cols]
    reject = out.loc[is_rejected, schema_cols]
    return clean, quar, reject


def transform_sales_orders(df: pd.DataFrame, batch_id: str, now: str):
    """
    Schema target: sales_order table
    Required NOT NULL: order_id, customer_id, order_date, created_at, etl_batch_id
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    out = pd.DataFrame()
    out["order_id"]         = df["source_order_id"].apply(deterministic_uuid)
    out["customer_id"]      = df["source_customer_id"].apply(deterministic_uuid)
    out["order_date"]       = df.get("order_date", pd.Series(dtype=str)).apply(parse_date_safe)
    out["order_status"]     = df.get("order_status", pd.Series(dtype=str)).apply(strip_or_none)
    out["currency"]         = df.get("currency", pd.Series(dtype=str)).apply(
        lambda v: str(v).strip().upper()[:3] if pd.notna(v) and str(v).strip() else None
    )
    out["order_total"]      = df.get("order_total", pd.Series(dtype=object)).apply(clean_numeric)
    out["created_at"]       = now
    out["updated_at"]       = None
    out["etl_batch_id"]     = batch_id
    out["source_system"]    = df["source_order_id"].apply(derive_source_system)
    out["source_record_id"] = df["source_order_id"].apply(strip_or_none)

    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    is_rejected = (
        out["order_id"].isna()
        | out["customer_id"].isna()
        | out["order_date"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    out = out.drop_duplicates(subset=["order_id"], keep="first")
    is_rejected = (
        out["order_id"].isna()
        | out["customer_id"].isna()
        | out["order_date"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    schema_cols = [
        "order_id", "customer_id", "order_date", "order_status", "currency",
        "order_total", "created_at", "updated_at",
        "etl_batch_id", "source_system", "source_record_id",
    ]

    clean  = out.loc[~is_rejected & ~is_quarantine, schema_cols]
    quar   = out.loc[is_quarantine, schema_cols]
    reject = out.loc[is_rejected, schema_cols]
    return clean, quar, reject


def transform_order_lines(df: pd.DataFrame, batch_id: str, now: str):
    """
    Schema target: order_line table
    Required NOT NULL: order_line_id, order_id, product_id, line_number, quantity, unit_price
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    out = pd.DataFrame()
    # Derive order_line_id from source_line_id if present, else composite
    if "source_line_id" in df.columns:
        out["order_line_id"] = df["source_line_id"].apply(deterministic_uuid)
    else:
        composite = df["source_order_id"].astype(str) + "_" + df["line_number"].astype(str)
        out["order_line_id"] = composite.apply(deterministic_uuid)

    out["order_id"]    = df["source_order_id"].apply(deterministic_uuid)
    out["product_id"]  = df["source_product_id"].apply(deterministic_uuid)
    out["line_number"] = pd.to_numeric(df.get("line_number"), errors="coerce")
    out["quantity"]    = df.get("quantity", pd.Series(dtype=object)).apply(clean_numeric)
    out["unit_price"]  = df.get("unit_price", pd.Series(dtype=object)).apply(clean_numeric)

    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    is_rejected = (
        out["order_line_id"].isna()
        | out["order_id"].isna()
        | out["product_id"].isna()
        | out["line_number"].isna()
        | out["quantity"].isna()
        | out["unit_price"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    out = out.drop_duplicates(subset=["order_id", "line_number"], keep="first")
    is_rejected = (
        out["order_line_id"].isna()
        | out["order_id"].isna()
        | out["product_id"].isna()
        | out["line_number"].isna()
        | out["quantity"].isna()
        | out["unit_price"].isna()
    )
    is_quarantine = (~is_rejected) & out["_dq_severity"].isin(["high", "med"])

    schema_cols = [
        "order_line_id", "order_id", "product_id",
        "line_number", "quantity", "unit_price",
    ]

    # cast int‑like columns
    for c in ("line_number", "quantity"):
        out[c] = out[c].apply(lambda v: int(v) if pd.notna(v) else v)

    clean  = out.loc[~is_rejected & ~is_quarantine, schema_cols]
    quar   = out.loc[is_quarantine, schema_cols]
    reject = out.loc[is_rejected, schema_cols]
    return clean, quar, reject

# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_splits(clean, quar, reject, output_dir, entity):
    """Write the three DataFrames as CSVs."""
    for subdir, frame in [("clean", clean), ("quarantine", quar), ("rejected", reject)]:
        path = os.path.join(output_dir, subdir)
        os.makedirs(path, exist_ok=True)
        fp = os.path.join(path, f"{entity}.csv")
        frame.to_csv(fp, index=False)
        print(f"  -> {subdir}/{entity}.csv  ({len(frame)} rows)")

# ---------------------------------------------------------------------------
# FK Cascade  -- move child rows whose parent FK is missing from clean
# ---------------------------------------------------------------------------

def _cascade_entity(output_dir, entity, fk_col, valid_parent_ids):
    """Move rows from clean -> quarantine if fk_col value is not in valid_parent_ids.

    Returns the count of rows moved.
    """
    clean_path = os.path.join(output_dir, "clean", f"{entity}.csv")
    quar_path  = os.path.join(output_dir, "quarantine", f"{entity}.csv")

    if not os.path.exists(clean_path):
        return 0

    clean = pd.read_csv(clean_path)
    if clean.empty:
        return 0

    orphan_mask = ~clean[fk_col].isin(valid_parent_ids)
    orphans     = clean[orphan_mask]
    survivors   = clean[~orphan_mask]

    if orphans.empty:
        return 0

    # Append orphans to quarantine
    if os.path.exists(quar_path):
        existing_quar = pd.read_csv(quar_path)
        updated_quar  = pd.concat([existing_quar, orphans], ignore_index=True)
    else:
        updated_quar = orphans

    survivors.to_csv(clean_path, index=False)
    updated_quar.to_csv(quar_path, index=False)

    return len(orphans)


def cascade_fk_integrity(output_dir):
    """Post-processing step: cascade FK constraints top-down.

    Order of dependency (parent -> child):
        etl_batch  -> contacts, customers, products, sales_orders
        contacts   -> customers        (via contact_id)
        customers  -> sales_orders     (via customer_id)
        sales_orders -> order_lines    (via order_id)
        products     -> order_lines    (via product_id)
    """
    print("-" * 50)
    print("  FK Cascade Post-Processing")
    print("-" * 50 + "\n")

    total_moved = 0

    # 1. contacts -> customers  (customer.contact_id must be in clean contacts)
    contacts_clean = pd.read_csv(os.path.join(output_dir, "clean", "contacts.csv"))
    valid_contacts = set(contacts_clean["contact_id"])
    n = _cascade_entity(output_dir, "customers", "contact_id", valid_contacts)
    print(f"  customers  : {n} rows moved to quarantine (orphan contact_id)")
    total_moved += n

    # 2. customers -> sales_orders  (sales_order.customer_id must be in clean customers)
    cust_clean = pd.read_csv(os.path.join(output_dir, "clean", "customers.csv"))
    valid_customers = set(cust_clean["customer_id"])
    n = _cascade_entity(output_dir, "sales_orders", "customer_id", valid_customers)
    print(f"  sales_orders: {n} rows moved to quarantine (orphan customer_id)")
    total_moved += n

    # 3. sales_orders -> order_lines  (order_line.order_id must be in clean sales_orders)
    orders_clean = pd.read_csv(os.path.join(output_dir, "clean", "sales_orders.csv"))
    valid_orders = set(orders_clean["order_id"])
    n = _cascade_entity(output_dir, "order_lines", "order_id", valid_orders)
    print(f"  order_lines : {n} rows moved to quarantine (orphan order_id)")
    total_moved += n

    # 4. products -> order_lines  (order_line.product_id must be in clean products)
    prods_clean = pd.read_csv(os.path.join(output_dir, "clean", "products.csv"))
    valid_products = set(prods_clean["product_id"])
    n = _cascade_entity(output_dir, "order_lines", "product_id", valid_products)
    print(f"  order_lines : {n} rows moved to quarantine (orphan product_id)")
    total_moved += n

    print(f"\n  Total rows cascaded to quarantine: {total_moved}\n")
    return total_moved

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Phase 2 - Silver Transformation")
    ap.add_argument("--input",  default="data/raw/bronze_simulated_messy/eg_crm")
    ap.add_argument("--output", default="data")
    args = ap.parse_args()

    batch_id   = str(uuid.uuid4())
    now        = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base       = args.input
    out        = args.output

    print("=" * 50)
    print("  Phase 2 - Silver Transformation Pipeline")
    print(f"  Batch : {batch_id}")
    print("=" * 50 + "\n")

    # --- ETL batch record ------------------------------------------------
    etl_batch = pd.DataFrame([{
        "etl_batch_id":    batch_id,
        "pipeline_run_id": f"transform_{batch_id[:8]}",
        "started_at":      now,
        "ended_at":        None,
        "status":          "running",
        "notes":           "Silver transformation run",
    }])
    os.makedirs(os.path.join(out, "clean"), exist_ok=True)
    etl_batch.to_csv(os.path.join(out, "clean", "etl_batch.csv"), index=False)
    print("[etl_batch] written\n")

    entities = {
        "contacts":     transform_contacts,
        "customers":    transform_customers,
        "products":     transform_products,
        "sales_orders": transform_sales_orders,
        "order_lines":  transform_order_lines,
    }

    for name, fn in entities.items():
        print(f"[{name}]")
        df = load_entity(base, name)
        if df.empty:
            print(f"  WARNING: no data found - skipping\n")
            continue
        print(f"  loaded {len(df)} raw rows")
        clean, quar, reject = fn(df, batch_id, now)
        write_splits(clean, quar, reject, out, name)
        print()

    # --- FK cascade post-processing --------------------------------------
    cascade_fk_integrity(out)

    # mark batch complete
    etl_batch["ended_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    etl_batch["status"]   = "completed"
    etl_batch.to_csv(os.path.join(out, "clean", "etl_batch.csv"), index=False)

    print("[OK] Transformation complete.")


if __name__ == "__main__":
    main()
