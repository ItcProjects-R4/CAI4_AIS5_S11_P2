"""
Validate Module
───────────────
Post-transform validation. Reads clean data from data/clean/,
runs all checks, writes quarantine to data/quarantine/ and
rejected to data/rejected/.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from etl.config import (
    CLEAN_FILES,
    QUARANTINE_FILES,
    REJECTED_FILES,
    FIELDS,
    REASON_FIELDS,
)
from etl.utils.logger import get_logger

log = get_logger("validate")


class ValidationResult:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.passed = True

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            self.passed = False

    def summary(self) -> str:
        lines = ["── Validation Report ──"]
        for c in self.checks:
            mark = "PASS" if c["passed"] else "FAIL"
            lines.append(f"  [{mark}] {c['check']}: {c['detail']}")
        return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    """Append rows to an existing CSV (or create if missing)."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _check_pk(rows: list[dict], pk: str, table: str, r: ValidationResult) -> tuple[list[dict], list[dict]]:
    """Return (clean_rows, duplicate_rows)."""
    seen: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        seen.setdefault(row.get(pk, ""), []).append(i)
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    if dups:
        r.add(f"{table}.PK uniqueness ({pk})", False, f"{len(dups)} duplicate keys")
        dup_idx = set()
        for indices in dups.values():
            dup_idx.update(indices[1:])
        clean = [row for i, row in enumerate(rows) if i not in dup_idx]
        dup_rows = [rows[i] for i in sorted(dup_idx)]
        return clean, dup_rows
    r.add(f"{table}.PK uniqueness ({pk})", True, f"all {len(rows)} unique")
    return rows, []


def _check_required(rows: list[dict], required: list[str], table: str, r: ValidationResult) -> tuple[list[dict], list[dict]]:
    """Return (clean, bad)."""
    bad = []
    clean = []
    for row in rows:
        missing = [f for f in required if not row.get(f)]
        if missing:
            bad.append(row | {"_quarantine_reason": f"missing required: {', '.join(missing)}"})
        else:
            clean.append(row)
    r.add(f"{table}.required fields", len(bad) == 0,
          f"{len(bad)} rows with missing fields" if bad else f"all {len(rows)} pass")
    return clean, bad


def _check_fk(child: list[dict], fk: str, parent: list[dict], pk: str,
              child_t: str, parent_t: str, r: ValidationResult) -> tuple[list[dict], list[dict]]:
    """Return (clean, orphans)."""
    parent_pks = {row.get(pk) for row in parent}
    orphans = []
    clean = []
    for row in child:
        if row.get(fk) not in parent_pks:
            orphans.append(row | {"_quarantine_reason": f"FK: {fk}={row.get(fk)} not in {parent_t}"})
        else:
            clean.append(row)
    r.add(f"{child_t} → {parent_t} FK ({fk})", len(orphans) == 0,
          f"{len(orphans)} orphans" if orphans else "0 orphans")
    return clean, orphans


def _merge_reasons(base: dict, extra: dict) -> dict:
    """Merge quarantine/reject reasons."""
    merged = dict(base)
    for key in ("_quarantine_reason", "_reject_reason"):
        if key in extra:
            existing = merged.get(key, "")
            merged[key] = f"{existing}; {extra[key]}" if existing else extra[key]
    return merged


def validate_all(transform_results: dict[str, dict[str, list[dict]]]) -> ValidationResult:
    r = ValidationResult()

    # Collect all rows that need quarantine/rejection
    all_quarantine: dict[str, list[dict]] = {t: [] for t in FIELDS}
    all_rejected: dict[str, list[dict]] = {t: [] for t in FIELDS}

    # Start with transform's clean output (transform already wrote to data/clean/)
    contacts = list(transform_results["contacts"]["clean"])
    customers = list(transform_results["customers"]["clean"])
    products = list(transform_results["products"]["clean"])
    orders = list(transform_results["sales_orders"]["clean"])
    lines = list(transform_results["order_lines"]["clean"])
    batches = list(transform_results["etl_batch"]["clean"])

    # ── PK uniqueness ──
    for tbl, pk, rows in [
        ("contacts", "contact_id", contacts),
        ("customers", "customer_id", customers),
        ("products", "product_id", products),
        ("sales_orders", "order_id", orders),
        ("order_lines", "order_line_id", lines),
    ]:
        clean, dups = _check_pk(rows, pk, tbl, r)
        if dups:
            all_quarantine[tbl].extend(dups)
        # Update the list
        if tbl == "contacts": contacts = clean
        elif tbl == "customers": customers = clean
        elif tbl == "products": products = clean
        elif tbl == "sales_orders": orders = clean
        elif tbl == "order_lines": lines = clean

    # ── Required fields ──
    for tbl, required, rows in [
        ("contacts", ["contact_id", "email"], contacts),
        ("customers", ["customer_id", "contact_id"], customers),
        ("products", ["product_id", "sku", "product_name"], products),
        ("sales_orders", ["order_id", "customer_id", "order_date"], orders),
        ("order_lines", ["order_line_id", "order_id", "product_id"], lines),
    ]:
        clean, bad = _check_required(rows, required, tbl, r)
        if bad:
            all_quarantine[tbl].extend(bad)
        if tbl == "contacts": contacts = clean
        elif tbl == "customers": customers = clean
        elif tbl == "products": products = clean
        elif tbl == "sales_orders": orders = clean
        elif tbl == "order_lines": lines = clean

    # ── Email uniqueness ──
    seen_emails: dict[str, list[int]] = {}
    for i, row in enumerate(contacts):
        email = row.get("email", "")
        seen_emails.setdefault(email, []).append(i)
    dup_emails = {e: idxs for e, idxs in seen_emails.items() if len(idxs) > 1}
    if dup_emails:
        dup_contact_ids = set()
        for idxs in dup_emails.values():
            dup_contact_ids.update(idxs[1:])
        dup_rows = [contacts[i] for i in sorted(dup_contact_ids)]
        for row in dup_rows:
            row["_quarantine_reason"] = f"duplicate email: {row.get('email', '')}"
        all_quarantine["contacts"].extend(dup_rows)
        # Remove customers referencing these contacts
        dup_cids = {row["contact_id"] for row in dup_rows}
        orphan_customers = [c for c in customers if c.get("contact_id") in dup_cids]
        for row in orphan_customers:
            row["_quarantine_reason"] = f"orphaned by duplicate contact email: {row.get('contact_id', '')}"
        all_quarantine["customers"].extend(orphan_customers)
        customers = [c for c in customers if c.get("contact_id") not in dup_cids]
        # Remove sales_orders referencing orphaned customers
        orphan_cids = {c["customer_id"] for c in orphan_customers}
        orphan_orders = [o for o in orders if o.get("customer_id") in orphan_cids]
        for row in orphan_orders:
            row["_quarantine_reason"] = f"orphaned by duplicate contact: order customer_id={row.get('customer_id', '')}"
        all_quarantine["sales_orders"].extend(orphan_orders)
        orders = [o for o in orders if o.get("customer_id") not in orphan_cids]
        # Remove order_lines referencing orphaned orders
        orphan_oids = {o["order_id"] for o in orphan_orders}
        orphan_lines = [l for l in lines if l.get("order_id") in orphan_oids]
        for row in orphan_lines:
            row["_quarantine_reason"] = f"orphaned by duplicate contact: order_line order_id={row.get('order_id', '')}"
        all_quarantine["order_lines"].extend(orphan_lines)
        lines = [l for l in lines if l.get("order_id") not in orphan_oids]
        contacts = [contacts[i] for i in range(len(contacts)) if i not in dup_contact_ids]
        r.add("contacts.email uniqueness", False, f"{len(dup_emails)} duplicate emails, {len(dup_rows)} rows quarantined")
    else:
        r.add("contacts.email uniqueness", True, "all emails unique")

    # ── SKU uniqueness (products) ──
    seen_skus: dict[str, list[int]] = {}
    for i, row in enumerate(products):
        sku = row.get("sku", "")
        seen_skus.setdefault(sku, []).append(i)
    dup_skus = {s: idxs for s, idxs in seen_skus.items() if len(idxs) > 1}
    if dup_skus:
        dup_product_ids = set()
        for idxs in dup_skus.values():
            dup_product_ids.update(idxs[1:])
        dup_prod_rows = [products[i] for i in sorted(dup_product_ids)]
        for row in dup_prod_rows:
            row["_quarantine_reason"] = f"duplicate sku: {row.get('sku', '')}"
        all_quarantine["products"].extend(dup_prod_rows)
        # Remove order_lines referencing these products
        dup_pids = {row["product_id"] for row in dup_prod_rows}
        orphan_lines = [l for l in lines if l.get("product_id") in dup_pids]
        for row in orphan_lines:
            row["_quarantine_reason"] = f"orphaned by duplicate product sku: {row.get('product_id', '')}"
        all_quarantine["order_lines"].extend(orphan_lines)
        lines = [l for l in lines if l.get("product_id") not in dup_pids]
        products = [products[i] for i in range(len(products)) if i not in dup_product_ids]
        r.add("products.sku uniqueness", False, f"{len(dup_skus)} duplicate skus, {len(dup_prod_rows)} rows quarantined")
    else:
        r.add("products.sku uniqueness", True, "all skus unique")

    # ── Email format ──
    bad_emails = [row for row in contacts if row.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", row["email"])]
    r.add("contacts.email format", len(bad_emails) == 0, f"{len(bad_emails)} invalid")
    if bad_emails:
        all_quarantine["contacts"].extend(bad_emails)
        contacts = [row for row in contacts if row not in bad_emails]

    # ── FK integrity ──
    clean, orphans = _check_fk(customers, "contact_id", contacts, "contact_id", "customers", "contacts", r)
    if orphans:
        all_quarantine["customers"].extend(orphans)
    customers = clean

    clean, orphans = _check_fk(orders, "customer_id", customers, "customer_id", "sales_orders", "customers", r)
    if orphans:
        all_quarantine["sales_orders"].extend(orphans)
    orders = clean

    clean, orphans = _check_fk(lines, "order_id", orders, "order_id", "order_lines", "sales_orders", r)
    if orphans:
        all_quarantine["order_lines"].extend(orphans)
    lines = clean

    clean, orphans = _check_fk(lines, "product_id", products, "product_id", "order_lines", "products", r)
    if orphans:
        all_quarantine["order_lines"].extend(orphans)
    lines = clean

    # ── Write final clean to data/clean/ (authoritative) ──
    _write_csv(CLEAN_FILES["etl_batch"], batches, FIELDS["etl_batch"])
    _write_csv(CLEAN_FILES["contacts"], contacts, FIELDS["contacts"])
    _write_csv(CLEAN_FILES["customers"], customers, FIELDS["customers"])
    _write_csv(CLEAN_FILES["products"], products, FIELDS["products"])
    _write_csv(CLEAN_FILES["sales_orders"], orders, FIELDS["sales_orders"])
    _write_csv(CLEAN_FILES["order_lines"], lines, FIELDS["order_lines"])

    # ── Append additional quarantine/rejected found by validation ──
    for tbl in ["contacts", "customers", "products", "sales_orders", "order_lines"]:
        fields = FIELDS[tbl] + REASON_FIELDS
        qr = all_quarantine[tbl]
        rr = all_rejected[tbl]
        if qr:
            _append_csv(QUARANTINE_FILES[tbl], qr, fields)
        if rr:
            _append_csv(REJECTED_FILES[tbl], rr, fields)

    log.info(r.summary())
    log.info("Final counts:")
    for tbl in ["contacts", "customers", "products", "sales_orders", "order_lines"]:
        q_count = len(all_quarantine.get(tbl, []))
        r_count = len(all_rejected.get(tbl, []))
        log.info("  %s: quarantine=%d rejected=%d", tbl, q_count, r_count)

    return r
