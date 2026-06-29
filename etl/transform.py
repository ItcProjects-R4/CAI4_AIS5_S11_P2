"""
Transform Module
────────────────
Cleans, normalises, and repairs raw data.

Output locations:
  data/clean/     — valid rows (overwrites source)
  data/quarantine/ — recoverable but suspicious rows
  data/rejected/  — unrecoverable rows
"""

from __future__ import annotations

import csv
import re
import uuid
from datetime import datetime
from pathlib import Path

from etl.config import (
    RAW_FILES,
    QUARANTINE_FILES,
    REJECTED_FILES,
    VALID_ORDER_STATUSES,
    VALID_SEGMENTS,
    VALID_CURRENCIES,
    VALID_STATUSES,
    PRODUCT_CATEGORIES_CANONICAL,
    DEPARTMENTS_CANONICAL,
    FIELDS,
    REASON_FIELDS,
)
from etl.utils.logger import get_logger

log = get_logger("transform")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Utility ────────────────────────────────────────────────────────

def _trim(val: str | None) -> str:
    return (val or "").strip()


def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False


def _is_valid_date(val: str) -> bool:
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            datetime.strptime(val.strip(), fmt)
            return True
        except (ValueError, TypeError):
            continue
    return False


def _parse_date(val: str) -> str | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(val.strip(), fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            continue
    return None


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)


# ── Table transforms ───────────────────────────────────────────────

def _t_etl_batch(rows: list[dict]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("etl_batch_id") or not _is_valid_uuid(r["etl_batch_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid etl_batch_id"})
            continue
        clean.append(r)
    return clean, quarantine, rejected


def _t_contacts(rows: list[dict]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("contact_id") or not _is_valid_uuid(r["contact_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid contact_id"})
            continue
        if not r.get("email"):
            rejected.append(r | {"_reject_reason": "missing email"})
            continue
        if not EMAIL_RE.match(r["email"]):
            quarantine.append(r | {"_quarantine_reason": "malformed email"})
            continue
        dept_key = r.get("department", "").strip().lower()
        if dept_key in DEPARTMENTS_CANONICAL:
            r["department"] = DEPARTMENTS_CANONICAL[dept_key]
        if r.get("country"):
            r["country"] = r["country"].strip().title()
        phone = r.get("phone", "")
        if phone:
            r["phone"] = re.sub(r"[^\d+\-\s()]", "", phone).strip() or phone
        clean.append(r)
    return clean, quarantine, rejected


def _t_customers(rows: list[dict], valid_contacts: set[str]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("customer_id") or not _is_valid_uuid(r["customer_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid customer_id"})
            continue
        if not r.get("contact_id") or not _is_valid_uuid(r["contact_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid contact_id"})
            continue
        if r["contact_id"] not in valid_contacts:
            quarantine.append(r | {"_quarantine_reason": f"FK violation: contact_id {r['contact_id']} not found"})
            continue
        status_key = r.get("status", "").strip().lower()
        if status_key in VALID_STATUSES:
            r["status"] = VALID_STATUSES[status_key][0]
        elif status_key:
            quarantine.append(r | {"_quarantine_reason": f"unknown status: {r['status']}"})
            continue
        seg_key = r.get("segment", "").strip().lower()
        if seg_key in VALID_SEGMENTS:
            r["segment"] = VALID_SEGMENTS[seg_key][0]
        elif r.get("segment"):
            quarantine.append(r | {"_quarantine_reason": f"unknown segment: {r['segment']}"})
            continue
        if r.get("customer_since") and not _is_valid_date(r["customer_since"]):
            parsed = _parse_date(r["customer_since"])
            if parsed:
                r["customer_since"] = parsed[:10]
            else:
                quarantine.append(r | {"_quarantine_reason": f"invalid customer_since: {r['customer_since']}"})
                continue
        clean.append(r)
    return clean, quarantine, rejected


def _t_products(rows: list[dict]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("product_id") or not _is_valid_uuid(r["product_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid product_id"})
            continue
        if not r.get("sku"):
            rejected.append(r | {"_reject_reason": "missing sku"})
            continue
        if not r.get("product_name"):
            rejected.append(r | {"_reject_reason": "missing product_name"})
            continue
        cat_key = r.get("category", "").strip().lower()
        if cat_key in PRODUCT_CATEGORIES_CANONICAL:
            r["category"] = PRODUCT_CATEGORIES_CANONICAL[cat_key]
        if r.get("brand"):
            r["brand"] = r["brand"].strip()
        try:
            price = float(r.get("list_price") or 0)
            if price < 0:
                quarantine.append(r | {"_quarantine_reason": f"negative list_price: {price}"})
                continue
            r["list_price"] = f"{price:.4f}"
        except (ValueError, TypeError):
            quarantine.append(r | {"_quarantine_reason": f"invalid list_price: {r.get('list_price')}"})
            continue
        raw_active = r.get("is_active", "").strip().lower()
        r["is_active"] = "1" if raw_active in ("1", "true", "yes", "") else "0"
        clean.append(r)
    return clean, quarantine, rejected


def _t_sales_orders(rows: list[dict], valid_customers: set[str]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("order_id") or not _is_valid_uuid(r["order_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid order_id"})
            continue
        if not r.get("customer_id") or not _is_valid_uuid(r["customer_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid customer_id"})
            continue
        if r["customer_id"] not in valid_customers:
            quarantine.append(r | {"_quarantine_reason": f"FK violation: customer_id {r['customer_id']} not found"})
            continue
        if not r.get("order_date"):
            rejected.append(r | {"_reject_reason": "missing order_date"})
            continue
        if not _is_valid_date(r["order_date"]):
            parsed = _parse_date(r["order_date"])
            if parsed:
                r["order_date"] = parsed
            else:
                quarantine.append(r | {"_quarantine_reason": f"invalid order_date: {r['order_date']}"})
                continue
        status_lower = r.get("order_status", "").strip().lower()
        matched = False
        for canonical, variants in VALID_ORDER_STATUSES.items():
            if status_lower in [v.lower() for v in variants]:
                r["order_status"] = canonical.capitalize()
                matched = True
                break
        if not matched and r.get("order_status"):
            quarantine.append(r | {"_quarantine_reason": f"unknown order_status: {r['order_status']}"})
            continue
        if r.get("currency"):
            r["currency"] = r["currency"].strip().upper()
        if r.get("currency") and r["currency"] not in VALID_CURRENCIES:
            quarantine.append(r | {"_quarantine_reason": f"unknown currency: {r['currency']}"})
            continue
        try:
            total = float(r.get("order_total") or 0)
            if total < 0:
                quarantine.append(r | {"_quarantine_reason": f"negative order_total: {total}"})
                continue
            r["order_total"] = f"{total:.4f}"
        except (ValueError, TypeError):
            r["order_total"] = "0.0000"
        clean.append(r)
    return clean, quarantine, rejected


def _t_order_lines(rows: list[dict], valid_orders: set[str], valid_products: set[str]):
    clean, quarantine, rejected = [], [], []
    for r in rows:
        r = {k: _trim(v) for k, v in r.items()}
        if not r.get("order_line_id") or not _is_valid_uuid(r["order_line_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid order_line_id"})
            continue
        if not r.get("order_id") or not _is_valid_uuid(r["order_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid order_id"})
            continue
        if not r.get("product_id") or not _is_valid_uuid(r["product_id"]):
            rejected.append(r | {"_reject_reason": "missing or invalid product_id"})
            continue
        if r["order_id"] not in valid_orders:
            quarantine.append(r | {"_quarantine_reason": f"FK violation: order_id {r['order_id']} not found"})
            continue
        if r["product_id"] not in valid_products:
            quarantine.append(r | {"_quarantine_reason": f"FK violation: product_id {r['product_id']} not found"})
            continue
        try:
            ln = int(r.get("line_number") or 0)
            if ln <= 0:
                quarantine.append(r | {"_quarantine_reason": f"invalid line_number: {ln}"})
                continue
            r["line_number"] = str(ln)
        except (ValueError, TypeError):
            rejected.append(r | {"_reject_reason": f"non-numeric line_number: {r.get('line_number')}"})
            continue
        try:
            qty = int(float(r.get("quantity") or 0))
            if qty <= 0:
                quarantine.append(r | {"_quarantine_reason": f"quantity <= 0: {qty}"})
                continue
            r["quantity"] = str(qty)
        except (ValueError, TypeError):
            rejected.append(r | {"_reject_reason": f"non-numeric quantity: {r.get('quantity')}"})
            continue
        try:
            price = float(r.get("unit_price") or 0)
            if price < 0:
                quarantine.append(r | {"_quarantine_reason": f"negative unit_price: {price}"})
                continue
            r["unit_price"] = f"{price:.4f}"
        except (ValueError, TypeError):
            rejected.append(r | {"_reject_reason": f"non-numeric unit_price: {r.get('unit_price')}"})
            continue
        clean.append(r)
    return clean, quarantine, rejected


# ── Main entry ─────────────────────────────────────────────────────

def transform_all(raw_data: dict[str, list[dict]]) -> dict[str, dict[str, list[dict]]]:
    """
    Transform all tables. Writes quarantine/rejected.
    Clean CSVs are written by validate.py after all checks pass.
    """
    results: dict[str, dict[str, list[dict]]] = {}

    log.info("Transforming ETL batch …")
    c, q, rj = _t_etl_batch(raw_data.get("etl_batch", []))
    results["etl_batch"] = {"clean": c, "quarantine": q, "rejected": rj}
    log.info("Transforming contacts …")
    c, q, rj = _t_contacts(raw_data.get("contacts", []))
    results["contacts"] = {"clean": c, "quarantine": q, "rejected": rj}
    valid_contacts = {r["contact_id"] for r in c}

    log.info("Transforming customers …")
    c, q, rj = _t_customers(raw_data.get("customers", []), valid_contacts)
    results["customers"] = {"clean": c, "quarantine": q, "rejected": rj}
    valid_customers = {r["customer_id"] for r in c}

    log.info("Transforming products …")
    c, q, rj = _t_products(raw_data.get("products", []))
    results["products"] = {"clean": c, "quarantine": q, "rejected": rj}
    valid_products = {r["product_id"] for r in c}

    log.info("Transforming sales orders …")
    c, q, rj = _t_sales_orders(raw_data.get("sales_orders", []), valid_customers)
    results["sales_orders"] = {"clean": c, "quarantine": q, "rejected": rj}
    valid_orders = {r["order_id"] for r in c}

    log.info("Transforming order lines …")
    c, q, rj = _t_order_lines(raw_data.get("order_lines", []), valid_orders, valid_products)
    results["order_lines"] = {"clean": c, "quarantine": q, "rejected": rj}

    for t, d in results.items():
        log.info("  %s: clean=%d quarantine=%d rejected=%d",
                 t, len(d["clean"]), len(d["quarantine"]), len(d["rejected"]))

    # Write quarantine + rejected so reconcile can count them
    for table in ["contacts", "customers", "products", "sales_orders", "order_lines"]:
        qr = results[table]["quarantine"]
        rr = results[table]["rejected"]
        all_f = FIELDS[table] + REASON_FIELDS
        if qr:
            _write_csv(QUARANTINE_FILES[table], qr, all_f)
        if rr:
            _write_csv(REJECTED_FILES[table], rr, all_f)

    return results
