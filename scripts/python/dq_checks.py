"""
Phase 3 - Data Quality (DQ) Validation & Reporting
====================================================
Runs AFTER transformation (Phase 2) to validate the Silver-layer CSVs
and produce a DQ summary report.

Validation rules:
    3.1a  Required fields      - IDs and NOT NULL columns must exist
    3.1b  Email format          - contains @ and . after trim
    3.1c  Phone format          - length 7-30, allowed chars only
    3.1d  Uniqueness            - email, SKU, (order_id, line_number)

Outputs:
    data/clean/dq_report.json   - structured DQ report
    stdout                       - human-readable summary

Usage:
    python scripts/python/dq_checks.py
    python scripts/python/dq_checks.py --output data
"""

import os, re, json, argparse, datetime
import pandas as pd


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def check_email(email: str) -> bool:
    """Basic email check: non-empty, contains @ and . after trim."""
    if pd.isna(email):
        return False
    e = str(email).strip()
    return "@" in e and "." in e and len(e) >= 5


PHONE_PATTERN = re.compile(r'^[\d\s\+\-\(\)\.x#]+$')

def check_phone(phone: str) -> bool:
    """Basic phone check: 7-30 chars, only digits/spaces/+-().x#."""
    if pd.isna(phone):
        return True  # phone is nullable
    p = str(phone).strip()
    if not p:
        return True  # empty is fine (nullable)
    return 7 <= len(p) <= 30 and bool(PHONE_PATTERN.match(p))


# ---------------------------------------------------------------------------
# Per-entity validators
# ---------------------------------------------------------------------------

def validate_contacts(df: pd.DataFrame) -> list[dict]:
    """Return list of DQ issue dicts for contacts."""
    issues = []
    for idx, row in df.iterrows():
        # Required: contact_id, email
        if pd.isna(row.get("contact_id")) or not str(row.get("contact_id", "")).strip():
            issues.append({"row": idx, "field": "contact_id", "code": "MISSING_REQUIRED_ID", "value": ""})
        if pd.isna(row.get("etl_batch_id")) or not str(row.get("etl_batch_id", "")).strip():
            issues.append({"row": idx, "field": "etl_batch_id", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        if pd.isna(row.get("email")) or not str(row.get("email", "")).strip():
            issues.append({"row": idx, "field": "email", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        elif not check_email(row["email"]):
            issues.append({"row": idx, "field": "email", "code": "INVALID_EMAIL_FORMAT", "value": str(row["email"])})
        # Phone format
        if not check_phone(row.get("phone")):
            issues.append({"row": idx, "field": "phone", "code": "INVALID_PHONE_FORMAT", "value": str(row.get("phone", ""))})
    return issues


def validate_customers(df: pd.DataFrame) -> list[dict]:
    issues = []
    for idx, row in df.iterrows():
        if pd.isna(row.get("customer_id")) or not str(row.get("customer_id", "")).strip():
            issues.append({"row": idx, "field": "customer_id", "code": "MISSING_REQUIRED_ID", "value": ""})
        if pd.isna(row.get("contact_id")) or not str(row.get("contact_id", "")).strip():
            issues.append({"row": idx, "field": "contact_id", "code": "MISSING_REQUIRED_FK", "value": ""})
        if pd.isna(row.get("etl_batch_id")) or not str(row.get("etl_batch_id", "")).strip():
            issues.append({"row": idx, "field": "etl_batch_id", "code": "MISSING_REQUIRED_FIELD", "value": ""})
    return issues


def validate_products(df: pd.DataFrame) -> list[dict]:
    issues = []
    for idx, row in df.iterrows():
        if pd.isna(row.get("product_id")) or not str(row.get("product_id", "")).strip():
            issues.append({"row": idx, "field": "product_id", "code": "MISSING_REQUIRED_ID", "value": ""})
        if pd.isna(row.get("sku")) or not str(row.get("sku", "")).strip():
            issues.append({"row": idx, "field": "sku", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        if pd.isna(row.get("product_name")) or not str(row.get("product_name", "")).strip():
            issues.append({"row": idx, "field": "product_name", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        if pd.isna(row.get("etl_batch_id")) or not str(row.get("etl_batch_id", "")).strip():
            issues.append({"row": idx, "field": "etl_batch_id", "code": "MISSING_REQUIRED_FIELD", "value": ""})
    return issues


def validate_sales_orders(df: pd.DataFrame) -> list[dict]:
    issues = []
    for idx, row in df.iterrows():
        if pd.isna(row.get("order_id")) or not str(row.get("order_id", "")).strip():
            issues.append({"row": idx, "field": "order_id", "code": "MISSING_REQUIRED_ID", "value": ""})
        if pd.isna(row.get("customer_id")) or not str(row.get("customer_id", "")).strip():
            issues.append({"row": idx, "field": "customer_id", "code": "MISSING_REQUIRED_FK", "value": ""})
        if pd.isna(row.get("order_date")) or not str(row.get("order_date", "")).strip():
            issues.append({"row": idx, "field": "order_date", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        if pd.isna(row.get("etl_batch_id")) or not str(row.get("etl_batch_id", "")).strip():
            issues.append({"row": idx, "field": "etl_batch_id", "code": "MISSING_REQUIRED_FIELD", "value": ""})
    return issues


def validate_order_lines(df: pd.DataFrame) -> list[dict]:
    issues = []
    for idx, row in df.iterrows():
        for fld in ["order_line_id", "order_id", "product_id"]:
            if pd.isna(row.get(fld)) or not str(row.get(fld, "")).strip():
                issues.append({"row": idx, "field": fld, "code": "MISSING_REQUIRED_ID", "value": ""})
        if pd.isna(row.get("line_number")) or not str(row.get("line_number", "")).strip():
            issues.append({"row": idx, "field": "line_number", "code": "MISSING_REQUIRED_FIELD", "value": ""})
        if pd.isna(row.get("quantity")) or row.get("quantity", 0) <= 0:
            issues.append({"row": idx, "field": "quantity", "code": "INVALID_QUANTITY", "value": str(row.get("quantity", ""))})
        if pd.isna(row.get("unit_price")) or row.get("unit_price", -1) < 0:
            issues.append({"row": idx, "field": "unit_price", "code": "INVALID_PRICE", "value": str(row.get("unit_price", ""))})
    return issues


# ---------------------------------------------------------------------------
# Uniqueness checks (run on clean data)
# ---------------------------------------------------------------------------

def check_uniqueness(output_dir: str) -> list[dict]:
    """Check uniqueness constraints on the clean CSVs."""
    issues = []

    contacts = pd.read_csv(os.path.join(output_dir, "clean", "contacts.csv"))
    dup_email = contacts[contacts.duplicated(subset=["email"], keep=False)]
    for _, row in dup_email.iterrows():
        issues.append({"entity": "contacts", "field": "email", "code": "DUPLICATE_EMAIL",
                        "value": str(row["email"])})

    products = pd.read_csv(os.path.join(output_dir, "clean", "products.csv"))
    dup_sku = products[products.duplicated(subset=["sku"], keep=False)]
    for _, row in dup_sku.iterrows():
        issues.append({"entity": "products", "field": "sku", "code": "DUPLICATE_SKU",
                        "value": str(row["sku"])})

    order_lines = pd.read_csv(os.path.join(output_dir, "clean", "order_lines.csv"))
    dup_ol = order_lines[order_lines.duplicated(subset=["order_id", "line_number"], keep=False)]
    for _, row in dup_ol.iterrows():
        issues.append({"entity": "order_lines", "field": "order_id+line_number",
                        "code": "DUPLICATE_ORDER_LINE",
                        "value": f"{row['order_id']}|{row['line_number']}"})

    return issues


# ---------------------------------------------------------------------------
# Main DQ report
# ---------------------------------------------------------------------------

def generate_dq_report(output_dir: str) -> dict:
    """Run all DQ checks and generate a structured report."""

    report = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entities": {},
        "uniqueness_issues": [],
        "top_error_codes": [],
    }

    all_error_codes = []

    entity_validators = {
        "contacts":     validate_contacts,
        "customers":    validate_customers,
        "products":     validate_products,
        "sales_orders": validate_sales_orders,
        "order_lines":  validate_order_lines,
    }

    for entity, validator in entity_validators.items():
        clean_path = os.path.join(output_dir, "clean", f"{entity}.csv")
        quar_path  = os.path.join(output_dir, "quarantine", f"{entity}.csv")
        rej_path   = os.path.join(output_dir, "rejected", f"{entity}.csv")

        clean_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else pd.DataFrame()
        quar_df  = pd.read_csv(quar_path)  if os.path.exists(quar_path)  else pd.DataFrame()
        rej_df   = pd.read_csv(rej_path)   if os.path.exists(rej_path)   else pd.DataFrame()

        total = len(clean_df) + len(quar_df) + len(rej_df)

        # Validate clean data for format issues
        clean_issues = validator(clean_df) if not clean_df.empty else []
        for iss in clean_issues:
            all_error_codes.append(iss["code"])

        report["entities"][entity] = {
            "total_rows_processed": total,
            "valid_rows":           len(clean_df),
            "quarantined_rows":     len(quar_df),
            "rejected_rows":        len(rej_df),
            "format_issues_in_clean": len(clean_issues),
            "issue_details":        clean_issues[:20],  # cap detail output
        }

    # Uniqueness checks
    uniq_issues = check_uniqueness(output_dir)
    report["uniqueness_issues"] = uniq_issues
    for iss in uniq_issues:
        all_error_codes.append(iss["code"])

    # Top 10 error codes
    from collections import Counter
    code_counts = Counter(all_error_codes)
    report["top_error_codes"] = [
        {"code": code, "count": count}
        for code, count in code_counts.most_common(10)
    ]

    return report


def print_report(report: dict):
    """Print a human-readable DQ summary."""
    print("=" * 60)
    print("  Phase 3 - Data Quality Report")
    print(f"  Generated: {report['generated_at']}")
    print("=" * 60 + "\n")

    print(f"{'Entity':<16} {'Total':>8} {'Valid':>8} {'Quarantine':>12} {'Rejected':>10} {'DQ Issues':>10}")
    print("-" * 66)
    for entity, data in report["entities"].items():
        print(f"{entity:<16} {data['total_rows_processed']:>8} {data['valid_rows']:>8} "
              f"{data['quarantined_rows']:>12} {data['rejected_rows']:>10} "
              f"{data['format_issues_in_clean']:>10}")

    print()
    if report["uniqueness_issues"]:
        print(f"Uniqueness violations: {len(report['uniqueness_issues'])}")
    else:
        print("Uniqueness violations: 0 (PASS)")

    print()
    if report["top_error_codes"]:
        print("Top Error Codes:")
        for item in report["top_error_codes"]:
            print(f"  {item['code']:<35} {item['count']:>5}")
    else:
        print("No errors found - all clean data passes DQ checks!")

    print()
    # Overall verdict
    total_issues = sum(d["format_issues_in_clean"] for d in report["entities"].values())
    total_uniq   = len(report["uniqueness_issues"])
    if total_issues == 0 and total_uniq == 0:
        print("[PASS] All clean data passes data quality validation.")
    else:
        print(f"[WARN] {total_issues + total_uniq} DQ issues found in clean data.")


def main():
    ap = argparse.ArgumentParser(description="Phase 3 - DQ Validation")
    ap.add_argument("--output", default="data")
    args = ap.parse_args()

    report = generate_dq_report(args.output)

    # Write JSON report
    report_path = os.path.join(args.output, "clean", "dq_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print_report(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
