"""
CRM ETL – Supplementary Download Script
========================================
Thin wrapper that downloads the same CRM-relevant endpoints used by the
main ``extract.py`` script, using a declarative DownloadTarget approach.

Sources (ERD-aligned only):
    DummyJSON   →  users, products, carts
    Northwind   →  Customers, Products, Orders, Order_Details

Output:  data/raw/<source>_<entity>_<YYYYMMDD>.json

NOTE: For production runs prefer ``extract.py`` which additionally
handles Northwind OData pagination and writes etl_batch metadata.
This script exists for quick, single-page re-downloads / debugging.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
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
RETRY_DELAY_SECONDS = 2
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Session
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DownloadTarget:
    source_name: str
    resource_name: str
    url: str
    output_path: Path


def create_session() -> requests.Session:
    """Create a reusable HTTP session for all API requests."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "CRM-ETL-Downloader/2.0",
        "Accept": "application/json",
    })
    return session


SESSION = create_session()

# ──────────────────────────────────────────────────────────────────────
# Endpoint registry — CRM-relevant only
# ──────────────────────────────────────────────────────────────────────
NORTHWIND_BASE = "https://services.odata.org/V4/Northwind/Northwind.svc"


def get_download_targets() -> tuple[DownloadTarget, ...]:
    """Return all configured CRM API endpoints and output locations."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    return (
        # DummyJSON
        DownloadTarget(
            source_name="dummyjson",
            resource_name="users",
            url="https://dummyjson.com/users?limit=0",
            output_path=RAW_DIR / f"dummyjson_users_{date_str}.json",
        ),
        DownloadTarget(
            source_name="dummyjson",
            resource_name="products",
            url="https://dummyjson.com/products?limit=0",
            output_path=RAW_DIR / f"dummyjson_products_{date_str}.json",
        ),
        DownloadTarget(
            source_name="dummyjson",
            resource_name="carts",
            url="https://dummyjson.com/carts?limit=0",
            output_path=RAW_DIR / f"dummyjson_carts_{date_str}.json",
        ),
        # Northwind OData V4
        DownloadTarget(
            source_name="northwind",
            resource_name="customers",
            url=f"{NORTHWIND_BASE}/Customers?$format=json",
            output_path=RAW_DIR / f"northwind_customers_{date_str}.json",
        ),
        DownloadTarget(
            source_name="northwind",
            resource_name="products",
            url=f"{NORTHWIND_BASE}/Products?$format=json",
            output_path=RAW_DIR / f"northwind_products_{date_str}.json",
        ),
        DownloadTarget(
            source_name="northwind",
            resource_name="orders",
            url=f"{NORTHWIND_BASE}/Orders?$format=json",
            output_path=RAW_DIR / f"northwind_orders_{date_str}.json",
        ),
        DownloadTarget(
            source_name="northwind",
            resource_name="order_details",
            url=f"{NORTHWIND_BASE}/Order_Details?$format=json",
            output_path=RAW_DIR / f"northwind_order_details_{date_str}.json",
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# Fetch & save helpers
# ──────────────────────────────────────────────────────────────────────

def fetch_json(url: str) -> Any | None:
    """Fetch JSON from *url* with retry and timeout handling."""
    for attempt in range(1, MAX_RETRIES + 1):
        LOGGER.info("Requesting %s | attempt %s/%s", url, attempt, MAX_RETRIES)
        try:
            response = SESSION.get(url, timeout=TIMEOUT_SECONDS)
        except requests.exceptions.Timeout as exc:
            LOGGER.warning("Timeout | %s | %s", url, exc)
        except requests.exceptions.RequestException as exc:
            LOGGER.warning("Request failed | %s | %s", url, exc)
        else:
            LOGGER.info("HTTP %s | %s", response.status_code, url)
            if response.status_code != 200:
                LOGGER.error("Non-200 status | url=%s | status=%s", url, response.status_code)
            else:
                try:
                    return response.json()
                except ValueError as exc:
                    LOGGER.error("Invalid JSON | url=%s | %s", url, exc)

        if attempt < MAX_RETRIES:
            LOGGER.info("Retrying in %ds …", RETRY_DELAY_SECONDS)
            time.sleep(RETRY_DELAY_SECONDS)

    return None


def save_json(payload: Any, output_path: Path) -> bool:
    """Save JSON payload to disk and verify the file was written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    except (TypeError, ValueError, OSError) as exc:
        LOGGER.error("Failed to write | path=%s | %s", output_path, exc)
        return False

    size = output_path.stat().st_size
    if size == 0:
        LOGGER.error("Written file is empty | path=%s", output_path)
        return False

    LOGGER.info("Saved %s | %d bytes", output_path.name, size)
    return True


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Download all CRM-relevant API endpoints to data/raw/."""
    LOGGER.info("Starting CRM raw data download")

    success_count = 0
    fail_count = 0

    for target in get_download_targets():
        LOGGER.info(
            "Downloading | source=%s | entity=%s",
            target.source_name, target.resource_name,
        )
        payload = fetch_json(target.url)
        if payload is None:
            LOGGER.error("FAILED %s/%s", target.source_name, target.resource_name)
            fail_count += 1
            continue

        if save_json(payload, target.output_path):
            success_count += 1
        else:
            fail_count += 1

    LOGGER.info(
        "Download finished | success=%d | failed=%d",
        success_count, fail_count,
    )
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
