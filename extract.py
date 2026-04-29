"""
CRM ETL – Bronze Raw Extraction Layer
======================================
Extracts upstream data for the CRM ERD (CONTACT, CUSTOMER, PRODUCT,
SALES_ORDER, ORDER_LINE) from two source systems:

    DummyJSON   →  users, products, carts
    Northwind   →  Customers, Products, Orders, Order_Details

Output contract
    Folder  :  data/raw/
    Naming  :  <source_system>_<entity>_<YYYYMMDD>.json
    Batch   :  data/raw/etl_batch_<YYYYMMDD>.json

Completeness guarantees
    • DummyJSON  – limit=0 fetches the full dataset in one request.
    • Northwind  – OData V4 pagination via @odata.nextLink until exhausted.
                   All "value" arrays are concatenated into one list.
                   @odata.context is preserved; @odata.nextLink is removed
                   from the final snapshot.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"

TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
INITIAL_BACKOFF = 2          # seconds; doubles on each retry

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Endpoint registry — only ERD-relevant sources
# ──────────────────────────────────────────────────────────────────────
NORTHWIND_BASE = "https://services.odata.org/V4/Northwind/Northwind.svc"

ENDPOINTS: list[dict[str, str]] = [
    # DummyJSON
    {"source": "dummyjson", "entity": "users",         "url": "https://dummyjson.com/users?limit=0"},
    {"source": "dummyjson", "entity": "products",      "url": "https://dummyjson.com/products?limit=0"},
    {"source": "dummyjson", "entity": "carts",         "url": "https://dummyjson.com/carts?limit=0"},
    # Northwind OData V4
    {"source": "northwind", "entity": "customers",     "url": f"{NORTHWIND_BASE}/Customers?$format=json"},
    {"source": "northwind", "entity": "products",      "url": f"{NORTHWIND_BASE}/Products?$format=json"},
    {"source": "northwind", "entity": "orders",        "url": f"{NORTHWIND_BASE}/Orders?$format=json"},
    {"source": "northwind", "entity": "order_details", "url": f"{NORTHWIND_BASE}/Order_Details?$format=json"},
]

# ──────────────────────────────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────────────────────────────

def _create_session() -> requests.Session:
    """Create a reusable HTTP session with standard headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "CRM-ETL-Extractor/1.0",
        "Accept": "application/json",
    })
    return session


SESSION = _create_session()


def _request_with_retry(url: str, *, timeout: int = TIMEOUT_SECONDS) -> dict:
    """GET *url*, parse JSON, retry with exponential backoff on failure."""
    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("GET %s | attempt %d/%d", url, attempt, MAX_RETRIES)
        try:
            resp = SESSION.get(url, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            logger.info(
                "HTTP %d | %d bytes | url=%s",
                resp.status_code, len(resp.content), url,
            )
            return payload
        except requests.RequestException as exc:
            logger.warning("Request failed | attempt %d/%d | %s", attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                raise
            logger.info("Retrying in %ds …", backoff)
            time.sleep(backoff)
            backoff *= 2
    # unreachable, but satisfies type-checker
    raise RuntimeError("Max retries exceeded")

# ──────────────────────────────────────────────────────────────────────
# Source-specific fetchers
# ──────────────────────────────────────────────────────────────────────

def fetch_dummyjson(url: str) -> tuple[Any, int]:
    """Fetch a DummyJSON endpoint (limit=0 → full dataset, single page).

    Returns (raw_payload_dict, request_count).
    """
    payload = _request_with_retry(url)
    return payload, 1


def fetch_northwind(url: str) -> tuple[dict, int]:
    """Fetch a Northwind OData V4 endpoint, following @odata.nextLink.

    All "value" arrays are concatenated into one list.
    The first page's @odata.context is preserved in the final dict.
    @odata.nextLink is removed from the saved snapshot.

    Returns (assembled_payload_dict, request_count).
    """
    all_records: list[dict] = []
    context: str | None = None
    page = 0
    next_url: str | None = url

    while next_url is not None:
        page += 1
        payload = _request_with_retry(next_url)

        # Capture context from first page
        if context is None:
            context = payload.get("@odata.context")

        records = payload.get("value", [])
        all_records.extend(records)
        logger.info(
            "Northwind page %d | %d records this page | %d cumulative",
            page, len(records), len(all_records),
        )

        next_url = payload.get("@odata.nextLink")
        if next_url and not next_url.startswith("http"):
            next_url = f"{NORTHWIND_BASE}/{next_url}"

    # Build a clean snapshot: context + value, no nextLink
    result: dict[str, Any] = {}
    if context:
        result["@odata.context"] = context
    result["value"] = all_records
    return result, page

# ──────────────────────────────────────────────────────────────────────
# Writer
# ──────────────────────────────────────────────────────────────────────

def _save_json(payload: Any, path: Path) -> None:
    """Serialize *payload* to *path* as indented JSON (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    size = path.stat().st_size
    logger.info("Saved %s | %d bytes", path.name, size)

# ──────────────────────────────────────────────────────────────────────
# Record-count inspector (for batch metadata)
# ──────────────────────────────────────────────────────────────────────

def _count_records(payload: Any, source: str, entity: str) -> int:
    """Return the number of data records in a raw payload."""
    if isinstance(payload, list):
        return len(payload)

    if isinstance(payload, dict):
        # Northwind V4: top-level "value"
        if "value" in payload and isinstance(payload["value"], list):
            return len(payload["value"])
        # DummyJSON: keyed by entity name (users, products, carts)
        if entity in payload and isinstance(payload[entity], list):
            return len(payload[entity])

    return 0

# ──────────────────────────────────────────────────────────────────────
# Main extraction loop
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Extract all CRM-relevant entities and write dated snapshots."""
    run_date = datetime.now(timezone.utc)
    date_str = run_date.strftime("%Y%m%d")
    started_at = run_date.isoformat()

    logger.info("=== CRM ETL Extraction – %s ===", date_str)

    batch_entities: list[dict[str, Any]] = []
    overall_ok = True

    for ep in ENDPOINTS:
        source = ep["source"]
        entity = ep["entity"]
        url = ep["url"]
        entry: dict[str, Any] = {
            "source": source,
            "entity": entity,
            "url": url,
            "record_count": 0,
            "request_count": 0,
            "errors": [],
        }

        try:
            if source == "northwind":
                payload, req_count = fetch_northwind(url)
            else:
                payload, req_count = fetch_dummyjson(url)

            entry["request_count"] = req_count
            rec_count = _count_records(payload, source, entity)
            entry["record_count"] = rec_count

            if rec_count == 0:
                msg = f"Zero records returned for {source}/{entity}"
                logger.error(msg)
                entry["errors"].append(msg)
                overall_ok = False
                continue

            out_path = RAW_DIR / f"{source}_{entity}_{date_str}.json"
            _save_json(payload, out_path)
            entry["output_file"] = str(out_path.relative_to(BASE_DIR))

        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            logger.error("FAILED %s/%s | %s", source, entity, msg)
            entry["errors"].append(msg)
            overall_ok = False

        batch_entities.append(entry)

    # ── etl_batch metadata ────────────────────────────────────────────
    ended_at = datetime.now(timezone.utc).isoformat()
    batch_meta = {
        "run_date_utc": date_str,
        "started_at_utc": started_at,
        "ended_at_utc": ended_at,
        "status": "success" if overall_ok else "failed",
        "entities": batch_entities,
    }
    batch_path = RAW_DIR / f"etl_batch_{date_str}.json"
    _save_json(batch_meta, batch_path)

    # ── Final validation ──────────────────────────────────────────────
    expected_files = [f"{ep['source']}_{ep['entity']}_{date_str}.json" for ep in ENDPOINTS]
    missing = [f for f in expected_files if not (RAW_DIR / f).exists()]
    if missing:
        logger.error("MISSING snapshots: %s", missing)
        overall_ok = False

    empty = [f for f in expected_files if (RAW_DIR / f).exists() and (RAW_DIR / f).stat().st_size == 0]
    if empty:
        logger.error("EMPTY snapshots: %s", empty)
        overall_ok = False

    if overall_ok:
        logger.info("=== Extraction complete – all %d entities OK ===", len(ENDPOINTS))
    else:
        logger.error("=== Extraction FAILED – see errors above ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
