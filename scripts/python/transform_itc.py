"""
ITC CRM Transform
==================
Reads the denormalized ITC CRM CSV (order-level grain with embedded
customer, contact, product columns) and splits it into the 5 Silver
entities matching the shopOrder MySQL schema.

Output is MERGED into the existing data/clean, data/quarantine,
data/rejected directories alongside the eg_crm data.

Usage:
    python scripts/python/transform_itc.py
"""

import os, uuid, datetime, argparse
import pandas as pd
from transform import (
    deterministic_uuid, derive_source_system, strip_or_none,
    parse_date_safe, parse_date_to_date, clean_numeric,
    write_splits, cascade_fk_integrity,
)

# Use a different namespace so ITC UUIDs don't collide with eg_crm UUIDs
NAMESPACE_ITC = uuid.uuid5(uuid.NAMESPACE_OID, "shopOrder_itc")


def itc_uuid(seed: str) -> str:
    """Deterministic UUID for ITC source IDs."""
    if pd.isna(seed) or not str(seed).strip():
        return None
    return str(uuid.uuid5(NAMESPACE_ITC, str(seed).strip()))


def _cascade_itc(output_dir, entity, fk_col, valid_parent_ids, batch_id):
    """Move ITC-batch rows from clean -> quarantine if FK orphaned.

    Only cascades rows with matching etl_batch_id (ITC rows).
    Leaves eg_crm rows untouched.
    """
    clean_path = os.path.join(output_dir, "clean", f"{entity}.csv")
    quar_path  = os.path.join(output_dir, "quarantine", f"{entity}.csv")

    if not os.path.exists(clean_path):
        return 0

    clean = pd.read_csv(clean_path)
    if clean.empty:
        return 0

    # Only consider ITC rows for cascading
    if "etl_batch_id" in clean.columns:
        itc_mask = clean["etl_batch_id"] == batch_id
    else:
        # order_lines has no etl_batch_id — skip batch scoping
        itc_mask = pd.Series(True, index=clean.index)

    orphan_mask = itc_mask & ~clean[fk_col].isin(valid_parent_ids)
    orphans   = clean[orphan_mask]
    survivors = clean[~orphan_mask]

    if orphans.empty:
        return 0

    if os.path.exists(quar_path):
        existing_quar = pd.read_csv(quar_path)
        updated_quar  = pd.concat([existing_quar, orphans], ignore_index=True)
    else:
        updated_quar = orphans

    survivors.to_csv(clean_path, index=False)
    updated_quar.to_csv(quar_path, index=False)
    return len(orphans)


def _cascade_itc_ol_product(output_dir, valid_product_ids, valid_order_ids_after_cascade):
    """Cascade order_lines by product_id. Since OL has no etl_batch_id,
    we only cascade lines whose order_id is still in clean (i.e., ITC lines
    that survived the order_id cascade but have orphan product_ids).
    """
    clean_path = os.path.join(output_dir, "clean", "order_lines.csv")
    quar_path  = os.path.join(output_dir, "quarantine", "order_lines.csv")

    if not os.path.exists(clean_path):
        return 0

    clean = pd.read_csv(clean_path)
    if clean.empty:
        return 0

    orphan_mask = ~clean["product_id"].isin(valid_product_ids)
    orphans   = clean[orphan_mask]
    survivors = clean[~orphan_mask]

    if orphans.empty:
        return 0

    if os.path.exists(quar_path):
        existing_quar = pd.read_csv(quar_path)
        updated_quar  = pd.concat([existing_quar, orphans], ignore_index=True)
    else:
        updated_quar = orphans

    survivors.to_csv(clean_path, index=False)
    updated_quar.to_csv(quar_path, index=False)
    return len(orphans)


def transform_itc(input_path: str, output_dir: str):
    """Main ITC CRM transformation."""

    batch_id = str(uuid.uuid4())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 50)
    print("  ITC CRM - Silver Transformation")
    print(f"  Batch : {batch_id}")
    print("=" * 50 + "\n")

    # --- Load ---
    raw = pd.read_csv(input_path)
    print(f"Loaded {len(raw)} rows from ITC CRM\n")

    # === ETL BATCH ===
    etl_batch = pd.DataFrame([{
        "etl_batch_id":    batch_id,
        "pipeline_run_id": f"itc_transform_{batch_id[:8]}",
        "started_at":      now,
        "ended_at":        None,
        "status":          "running",
        "notes":           "ITC CRM transformation run",
    }])
    batch_path = os.path.join(output_dir, "clean", "etl_batch.csv")
    if os.path.exists(batch_path):
        existing = pd.read_csv(batch_path)
        pd.concat([existing, etl_batch], ignore_index=True).to_csv(batch_path, index=False)
    else:
        os.makedirs(os.path.join(output_dir, "clean"), exist_ok=True)
        etl_batch.to_csv(batch_path, index=False)
    print("[etl_batch] appended\n")

    # =====================================================================
    # 1. CONTACTS
    # =====================================================================
    print("[contacts]")
    contacts_raw = raw[[
        "contact_contact_id", "contact_email", "contact_full_name",
        "contact_phone", "contact_country", "contact_city",
        "contact_address_line1", "contact_company_name", "contact_job_title"
    ]].drop_duplicates(subset=["contact_contact_id"])

    contacts = pd.DataFrame()
    contacts["contact_id"]       = contacts_raw["contact_contact_id"].apply(itc_uuid)
    contacts["email"]            = contacts_raw["contact_email"].apply(strip_or_none)
    contacts["full_name"]        = contacts_raw["contact_full_name"].apply(strip_or_none)
    contacts["phone"]            = contacts_raw["contact_phone"].apply(strip_or_none)
    contacts["country"]          = contacts_raw["contact_country"].apply(strip_or_none)
    contacts["address_line1"]    = contacts_raw["contact_address_line1"].apply(strip_or_none)
    contacts["city"]             = contacts_raw["contact_city"].apply(strip_or_none)
    contacts["state"]            = None
    contacts["postal_code"]      = None
    contacts["company_name"]     = contacts_raw["contact_company_name"].apply(strip_or_none)
    contacts["department"]       = None
    contacts["job_title"]        = contacts_raw["contact_job_title"].apply(strip_or_none)
    contacts["attributes_json"]  = None
    contacts["created_at"]       = now
    contacts["updated_at"]       = None
    contacts["etl_batch_id"]     = batch_id
    contacts["source_system"]    = "itc_crm"
    contacts["source_record_id"] = contacts_raw["contact_contact_id"].apply(strip_or_none)

    # Rejection: missing contact_id or email
    is_rejected = contacts["contact_id"].isna() | contacts["email"].isna()
    # Dedup by email (keep first)
    contacts["_nulls"] = contacts.isnull().sum(axis=1)
    contacts = contacts.sort_values(["email", "_nulls"])
    contacts = contacts.drop_duplicates(subset=["email"], keep="first")
    is_rejected = contacts["contact_id"].isna() | contacts["email"].isna()

    schema = [c for c in contacts.columns if not c.startswith("_")]
    _write_entity(contacts, is_rejected, schema, output_dir, "contacts")

    # =====================================================================
    # 2. CUSTOMERS
    # =====================================================================
    print("[customers]")
    cust_raw = raw[[
        "customer_customer_id", "customer_contact_id",
        "customer_customer_since", "customer_status", "customer_segment"
    ]].drop_duplicates(subset=["customer_customer_id"])

    customers = pd.DataFrame()
    customers["customer_id"]      = cust_raw["customer_customer_id"].apply(itc_uuid)
    customers["contact_id"]       = cust_raw["customer_contact_id"].apply(itc_uuid)
    customers["customer_since"]   = cust_raw["customer_customer_since"].apply(parse_date_to_date)
    customers["status"]           = cust_raw["customer_status"].apply(strip_or_none)
    customers["segment"]          = cust_raw["customer_segment"].apply(strip_or_none)
    customers["created_at"]       = now
    customers["updated_at"]       = None
    customers["etl_batch_id"]     = batch_id
    customers["source_system"]    = "itc_crm"
    customers["source_record_id"] = cust_raw["customer_customer_id"].apply(strip_or_none)

    is_rejected = customers["customer_id"].isna() | customers["contact_id"].isna()
    customers = customers.drop_duplicates(subset=["customer_id"], keep="first")
    # Schema has UNIQUE KEY (contact_id) — only 1 customer per contact
    customers = customers.sort_values("customer_since", ascending=False, na_position="last")
    customers = customers.drop_duplicates(subset=["contact_id"], keep="first")
    is_rejected = customers["customer_id"].isna() | customers["contact_id"].isna()

    schema = list(customers.columns)
    _write_entity(customers, is_rejected, schema, output_dir, "customers")

    # =====================================================================
    # 3. PRODUCTS
    # =====================================================================
    print("[products]")
    prod_raw = raw[[
        "product_product_id", "product_product_name",
        "product_category", "product_brand", "product_list_price"
    ]].drop_duplicates(subset=["product_product_id"])

    products = pd.DataFrame()
    products["product_id"]       = prod_raw["product_product_id"].apply(itc_uuid)
    products["sku"]              = prod_raw["product_product_id"].apply(
        lambda v: f"ITC-{str(v).replace('P','')}" if pd.notna(v) else None
    )
    products["product_name"]     = prod_raw["product_product_name"].apply(strip_or_none)
    products["category"]         = prod_raw["product_category"].apply(strip_or_none)
    products["brand"]            = prod_raw["product_brand"].apply(strip_or_none)
    products["list_price"]       = prod_raw["product_list_price"].apply(clean_numeric)
    products["is_active"]        = 1
    products["attributes_json"]  = None
    products["created_at"]       = now
    products["updated_at"]       = None
    products["etl_batch_id"]     = batch_id
    products["source_system"]    = "itc_crm"
    products["source_record_id"] = prod_raw["product_product_id"].apply(strip_or_none)

    is_rejected = products["product_id"].isna() | products["sku"].isna() | products["product_name"].isna()
    products = products.drop_duplicates(subset=["sku"], keep="first")
    is_rejected = products["product_id"].isna() | products["sku"].isna() | products["product_name"].isna()

    schema = list(products.columns)
    _write_entity(products, is_rejected, schema, output_dir, "products")

    # =====================================================================
    # 4. SALES ORDERS
    # =====================================================================
    print("[sales_orders]")
    orders = pd.DataFrame()
    orders["order_id"]         = raw["order_order_id"].apply(itc_uuid)
    orders["customer_id"]      = raw["order_customer_id"].apply(itc_uuid)
    orders["order_date"]       = raw["order_order_date"].apply(parse_date_safe)
    orders["order_status"]     = raw["order_order_status"].apply(strip_or_none)
    orders["currency"]         = "EGP"  # ITC CRM is Egypt-based
    orders["order_total"]      = raw["order_order_total"].apply(clean_numeric)
    orders["created_at"]       = now
    orders["updated_at"]       = None
    orders["etl_batch_id"]     = batch_id
    orders["source_system"]    = "itc_crm"
    orders["source_record_id"] = raw["order_order_id"].apply(strip_or_none)

    is_rejected = orders["order_id"].isna() | orders["customer_id"].isna() | orders["order_date"].isna()
    orders = orders.drop_duplicates(subset=["order_id"], keep="first")
    is_rejected = orders["order_id"].isna() | orders["customer_id"].isna() | orders["order_date"].isna()

    schema = list(orders.columns)
    _write_entity(orders, is_rejected, schema, output_dir, "sales_orders")

    # =====================================================================
    # 5. ORDER LINES  (each ITC row = 1 order with 1 product = 1 line)
    # =====================================================================
    print("[order_lines]")
    ol = pd.DataFrame()
    composite_id = raw["order_order_id"].astype(str) + "_" + raw["product_product_id"].astype(str)
    ol["order_line_id"] = composite_id.apply(itc_uuid)
    ol["order_id"]      = raw["order_order_id"].apply(itc_uuid)
    ol["product_id"]    = raw["product_product_id"].apply(itc_uuid)
    ol["line_number"]   = 1
    # ITC has order_total but no quantity/unit_price breakdown,
    # so: quantity=1, unit_price=order_total (best available)
    ol["quantity"]      = 1
    ol["unit_price"]    = raw["order_order_total"].apply(clean_numeric)

    is_rejected = (
        ol["order_line_id"].isna() | ol["order_id"].isna()
        | ol["product_id"].isna() | ol["unit_price"].isna()
    )
    ol = ol.drop_duplicates(subset=["order_id", "line_number"], keep="first")
    is_rejected = (
        ol["order_line_id"].isna() | ol["order_id"].isna()
        | ol["product_id"].isna() | ol["unit_price"].isna()
    )

    schema = list(ol.columns)
    _write_entity(ol, is_rejected, schema, output_dir, "order_lines")

    # =====================================================================
    # FK CASCADE (ITC-scoped only — do not re-cascade eg_crm data)
    # =====================================================================
    print("-" * 50)
    print("  FK Cascade Post-Processing (ITC scope)")
    print("-" * 50 + "\n")

    total_moved = 0

    # Read clean files
    contacts_clean = pd.read_csv(os.path.join(output_dir, "clean", "contacts.csv"))
    valid_contacts = set(contacts_clean["contact_id"])

    # customers: cascade by orphan contact_id (ITC batch only)
    n = _cascade_itc(output_dir, "customers", "contact_id", valid_contacts, batch_id)
    print(f"  customers  : {n} rows moved to quarantine (orphan contact_id)")
    total_moved += n

    cust_clean = pd.read_csv(os.path.join(output_dir, "clean", "customers.csv"))
    valid_customers = set(cust_clean["customer_id"])

    # sales_orders: cascade by orphan customer_id (ITC batch only)
    n = _cascade_itc(output_dir, "sales_orders", "customer_id", valid_customers, batch_id)
    print(f"  sales_orders: {n} rows moved to quarantine (orphan customer_id)")
    total_moved += n

    orders_clean = pd.read_csv(os.path.join(output_dir, "clean", "sales_orders.csv"))
    valid_orders = set(orders_clean["order_id"])

    # order_lines: cascade by orphan order_id (ITC batch only)
    n = _cascade_itc(output_dir, "order_lines", "order_id", valid_orders, batch_id)
    print(f"  order_lines : {n} rows moved to quarantine (orphan order_id)")
    total_moved += n

    prods_clean = pd.read_csv(os.path.join(output_dir, "clean", "products.csv"))
    valid_products = set(prods_clean["product_id"])

    # order_lines: cascade by orphan product_id (ITC batch only — no etl_batch_id on OL, so use order_id scope)
    n = _cascade_itc_ol_product(output_dir, valid_products, valid_orders)
    print(f"  order_lines : {n} rows moved to quarantine (orphan product_id)")
    total_moved += n

    print(f"\n  Total rows cascaded to quarantine: {total_moved}\n")

    # Mark batch complete
    etl_batch["ended_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    etl_batch["status"]   = "completed"
    batch_df = pd.read_csv(batch_path)
    batch_df.loc[batch_df["etl_batch_id"] == batch_id, "ended_at"] = etl_batch["ended_at"].iloc[0]
    batch_df.loc[batch_df["etl_batch_id"] == batch_id, "status"] = "completed"
    batch_df.to_csv(batch_path, index=False)

    print("[OK] ITC CRM Transformation complete.")


def _write_entity(df, is_rejected, schema_cols, output_dir, entity):
    """Append ITC data to existing CSVs (merge with eg_crm data)."""
    clean  = df.loc[~is_rejected, schema_cols]
    reject = df.loc[is_rejected, schema_cols]
    # No DQ severity in ITC, so no quarantine from this source
    quar   = pd.DataFrame(columns=schema_cols)

    # Dedup key sets per entity to prevent cross-source collisions.
    # Each item in the list is one UNIQUE constraint to enforce.
    dedup_key_sets = {
        "contacts":     [["email"]],
        "customers":    [["customer_id"], ["contact_id"]],  # two separate UNIQUE constraints
        "products":     [["sku"]],
        "sales_orders": [["order_id"]],
        "order_lines":  [["order_id", "line_number"]],      # one composite UNIQUE
    }
    key_sets = dedup_key_sets.get(entity, [])

    for subdir, frame in [("clean", clean), ("quarantine", quar), ("rejected", reject)]:
        path = os.path.join(output_dir, subdir)
        os.makedirs(path, exist_ok=True)
        fp = os.path.join(path, f"{entity}.csv")

        if os.path.exists(fp) and os.path.getsize(fp) > 0:
            existing = pd.read_csv(fp)
            merged = pd.concat([existing, frame], ignore_index=True)
            # Deduplicate: keep existing (first) over new (ITC) on collision
            if key_sets and subdir == "clean":
                for ks in key_sets:
                    merged = merged.drop_duplicates(subset=ks, keep="first")
            merged.to_csv(fp, index=False)
        else:
            frame.to_csv(fp, index=False)

        print(f"  -> {subdir}/{entity}.csv  (+{len(frame)} rows, ITC)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ITC CRM Transform")
    ap.add_argument("--input", default="data/raw/ITC CRM_dataset_combined.csv")
    ap.add_argument("--output", default="data")
    args = ap.parse_args()
    transform_itc(args.input, args.output)
