"""
Phase 2 - Silver Transformation Pipeline
=========================================
Reads Bronze Simulated Messy JSON  ->  cleans / validates  ->  writes:
    data/clean/<entity>.csv        (ready for Gold / SQL load)
    data/quarantine/<entity>.csv   (recoverable issues, held for review)
    data/rejected/<entity>.csv     (unrecoverable, dropped from pipeline)

Column names in every output CSV match the MySQL schema exactly.
"""

import os, sys, glob, json, uuid, re, datetime, argparse, hashlib
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


PHONE_SCI_RE = re.compile(r"^[\+\-]?\d+(\.\d+)?[eE][\+\-]?\d+$")
PHONE_ALLOWED_RE = re.compile(r"^[\d\s\+\-\(\)\.x#]+$")


def normalize_phone(val):
    """Normalize phone values to a safe, DQ-friendly string."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None

    # Strip common stray quotes/apostrophes from Excel exports
    s = s.strip("\"'`")
    s = s.replace("'", "").replace('"', "")
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None

    # Convert scientific notation or trailing .0 into digits
    if PHONE_SCI_RE.match(s):
        try:
            num = float(s)
            if pd.isna(num):
                return None
            s = str(int(round(num)))
        except Exception:
            pass
    elif re.match(r"^\d+\.0$", s):
        s = s[:-2]

    if not s:
        return None
    if not PHONE_ALLOWED_RE.match(s):
        return None
    if len(s) < 7 or len(s) > 30:
        return None
    return s


ORDER_STATUS_MAP = {
    "completed": "Completed",
    "compelted": "Completed",
    "complete": "Completed",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "pending": "Pending",
    "processing": "Processing",
    "shipped": "Shipped",
    "returned": "Returned",
    "refunded": "Refunded",
}


def normalize_order_status(val):
    """Normalize order_status casing and common typos."""
    s = strip_or_none(val)
    if s is None:
        return None
    key = re.sub(r"\s+", " ", s).strip().lower()
    return ORDER_STATUS_MAP.get(key, s)


def _stable_int(seed, mod):
    raw = "" if seed is None else str(seed)
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % mod


def _clean_postal_code(val):
    if pd.isna(val) or not str(val).strip():
        return None
    digits = re.sub(r"\D", "", str(val))
    if len(digits) >= 5:
        return digits[:5]
    return None


def _arabic_to_latin(text):
    if pd.isna(text):
        return None
    s = str(text)
    if not s.strip():
        return None
    s = s.translate(ARABIC_DIGIT_MAP)
    s = s.replace("ـ", "")
    out = []
    for ch in s:
        if ch in ARABIC_CHAR_MAP:
            out.append(ARABIC_CHAR_MAP[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append(" ")
    s = "".join(out)
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def _gov_key(val):
    s = strip_or_none(val)
    if s is None:
        return ""
    s = re.sub(r"[-_/]", " ", str(s))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _normalize_state_name(val):
    s = strip_or_none(val)
    if s is None:
        return None
    if s in ARABIC_STATE_MAP:
        return ARABIC_STATE_MAP[s]
    latin = _arabic_to_latin(s) or s
    key = _gov_key(latin)
    alias = STATE_ALIAS_LOOKUP.get(key)
    if alias:
        return alias
    return EGYPT_GOVERNORATE_LOOKUP.get(key, latin)


def _normalize_city_name(val):
    s = strip_or_none(val)
    if s is None:
        return None
    latin = _arabic_to_latin(s) or s
    latin = re.sub(r"\s+", " ", latin).strip()
    return latin if latin else None


def _normalize_street_name(val):
    s = strip_or_none(val)
    if s is None:
        return None
    s = s.translate(ARABIC_DIGIT_MAP)
    if s.strip().lower() in {"(not checked)", "not checked"}:
        return None
    replacements = [
        ("امتداد شارع", "Extension of Street"),
        ("شارع", "Street"),
        ("حارة", "Alley"),
        ("زقاق", "Lane"),
        ("طريق", "Road"),
        ("ميدان", "Square"),
        ("كورنيش", "Corniche"),
        ("جادة", "Avenue"),
    ]
    for ar, en in replacements:
        s = s.replace(ar, en)
    latin = _arabic_to_latin(s) or s
    latin = re.sub(r"\s+", " ", latin).strip()
    return latin if latin else None


_EGYPT_ADDRESS_POOL = None


def _load_egypt_address_pool():
    global _EGYPT_ADDRESS_POOL
    if _EGYPT_ADDRESS_POOL is not None:
        return _EGYPT_ADDRESS_POOL

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_path = os.path.join(root, "data", "raw", "output.csv")
    eng_path = os.path.join(root, "data", "raw", "output_en.csv")

    if not os.path.exists(raw_path) and not os.path.exists(eng_path):
        _EGYPT_ADDRESS_POOL = []
        return _EGYPT_ADDRESS_POOL

    def _read_csv(path):
        return pd.read_csv(path, dtype=str)

    if os.path.exists(raw_path):
        df = _read_csv(raw_path)
    elif os.path.exists(eng_path):
        df = _read_csv(eng_path)
        raw_path = None
    else:
        _EGYPT_ADDRESS_POOL = []
        return _EGYPT_ADDRESS_POOL

    df = df.rename(columns=lambda c: str(c).strip())
    if "country" in df.columns:
        df["country"] = df["country"].apply(strip_or_none)
        df = df[df["country"].str.upper() == "EG"].copy()
    else:
        df = df.copy()

    if "state" in df.columns:
        df["state"] = df["state"].apply(_normalize_state_name)
    else:
        df["state"] = None

    if "city" in df.columns:
        df["city"] = df["city"].apply(_normalize_city_name)
    else:
        df["city"] = None

    if "postal_code" in df.columns:
        df["postal_code"] = df["postal_code"].apply(_clean_postal_code)
    else:
        df["postal_code"] = None

    if "street_name" in df.columns:
        df["street_name"] = df["street_name"].apply(_normalize_street_name)
    else:
        df["street_name"] = None

    df["country"] = "Egypt"
    if raw_path is not None:
        df.to_csv(eng_path, index=False)

    for col in ["state", "city", "postal_code", "street_name"]:
        if col not in df.columns:
            df[col] = None

    df = df[df["state"].notna() & df["street_name"].notna()].copy()
    df = df[df["state"].isin(EGYPT_GOVERNORATES)].copy()
    _EGYPT_ADDRESS_POOL = df.to_dict("records")
    return _EGYPT_ADDRESS_POOL


def _fake_egypt_phone(seed):
    prefix = ["010", "011", "012", "015"][_stable_int(f"{seed}|prefix", 4)]
    num = _stable_int(f"{seed}|phone", 100000000)
    return f"{prefix}{num:08d}"


def _fake_egypt_name(seed):
    first = EGYPT_FIRST_NAMES[_stable_int(f"{seed}|fname", len(EGYPT_FIRST_NAMES))]
    last = EGYPT_LAST_NAMES[_stable_int(f"{seed}|lname", len(EGYPT_LAST_NAMES))]
    return f"{first} {last}"


def enrich_egypt_contacts(df: pd.DataFrame) -> pd.DataFrame:
    """Replace Egypt contact fields with deterministic Egypt data from output.csv."""
    df = df.copy()
    is_egypt = df["country"].apply(
        lambda v: str(v).strip().lower() == "egypt" if pd.notna(v) else False
    )
    pool = _load_egypt_address_pool()
    if not pool:
        return df

    for idx, row in df[is_egypt].iterrows():
        seed = row.get("contact_id") or row.get("email") or row.get("source_record_id")
        addr_row = pool[_stable_int(f"{seed}|addr", len(pool))]
        state = addr_row.get("state")
        city = addr_row.get("city") or EGYPT_GOVERNORATE_CAPITALS.get(state, state)
        street = addr_row.get("street_name")
        postal = _clean_postal_code(addr_row.get("postal_code"))
        house_no = 1 + _stable_int(f"{seed}|house", 200)

        if street:
            df.at[idx, "address_line1"] = f"{house_no} {street}"
        df.at[idx, "state"] = state
        df.at[idx, "city"] = city
        df.at[idx, "postal_code"] = postal or f"{_stable_int(f'{seed}|postal', 100000):05d}"
        df.at[idx, "country"] = "Egypt"
        df.at[idx, "phone"] = _fake_egypt_phone(seed)
        df.at[idx, "full_name"] = _fake_egypt_name(seed)

    return df


# ---------------------------------------------------------------------------
# Geographic normalisation (Egypt-aware)
# ---------------------------------------------------------------------------

EGYPT_GOVERNORATES = {
    "Alexandria", "Aswan", "Asyut", "Beheira", "Beni Suef", "Cairo",
    "Dakahlia", "Damietta", "Faiyum", "Gharbia", "Giza", "Ismailia",
    "Kafr El Sheikh", "Luxor", "Matrouh", "Minya", "Monufia",
    "New Valley", "North Sinai", "Port Said", "Qalyubiya", "Qena",
    "Red Sea", "Sharqia", "Sohag", "South Sinai", "Suez",
}

EGYPT_GOVERNORATE_CAPITALS = {
    "Alexandria": "Alexandria",
    "Aswan": "Aswan",
    "Asyut": "Asyut",
    "Beheira": "Damanhur",
    "Beni Suef": "Beni Suef",
    "Cairo": "Cairo",
    "Dakahlia": "Mansoura",
    "Damietta": "Damietta",
    "Faiyum": "Faiyum",
    "Gharbia": "Tanta",
    "Giza": "Giza",
    "Ismailia": "Ismailia",
    "Kafr El Sheikh": "Kafr El Sheikh",
    "Luxor": "Luxor",
    "Matrouh": "Marsa Matruh",
    "Minya": "Minya",
    "Monufia": "Shibin El Kom",
    "New Valley": "Kharga Oasis",
    "North Sinai": "Arish",
    "Port Said": "Port Said",
    "Qalyubiya": "Banha",
    "Qena": "Qena",
    "Red Sea": "Hurghada",
    "Sharqia": "Zagazig",
    "Sohag": "Sohag",
    "South Sinai": "El Tor",
    "Suez": "Suez",
}

ARABIC_DIGIT_MAP = str.maketrans({
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
})

ARABIC_CHAR_MAP = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "a",
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h",
    "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t",
    "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "q",
    "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h",
    "و": "w", "ي": "y", "ى": "a", "ئ": "y", "ؤ": "w",
    "ة": "a", "ء": "",
}

ARABIC_STATE_MAP = {
    "القاهرة": "Cairo",
    "الإسكندرية": "Alexandria",
    "الاسكندرية": "Alexandria",
    "الإسماعيلية": "Ismailia",
    "الاسماعيلية": "Ismailia",
    "أسوان": "Aswan",
    "اسوان": "Aswan",
    "أسيوط": "Asyut",
    "اسيوط": "Asyut",
    "البحيرة": "Beheira",
    "بني سويف": "Beni Suef",
    "بورسعيد": "Port Said",
    "جنوب سيناء": "South Sinai",
    "الجيزة": "Giza",
    "الدقهلية": "Dakahlia",
    "دمياط": "Damietta",
    "سوهاج": "Sohag",
    "السويس": "Suez",
    "الشرقية": "Sharqia",
    "الغربية": "Gharbia",
    "الفيوم": "Faiyum",
    "القليوبية": "Qalyubiya",
    "قنا": "Qena",
    "كفر الشيخ": "Kafr El Sheikh",
    "مطروح": "Matrouh",
    "المنوفية": "Monufia",
    "المنيا": "Minya",
    "الوادي الجديد": "New Valley",
    "الأقصر": "Luxor",
    "الاقصر": "Luxor",
    "البحر الأحمر": "Red Sea",
    "البحر الاحمر": "Red Sea",
    "شمال سيناء": "North Sinai",
}

EGYPT_GOVERNORATE_LOOKUP = {
    _gov_key(gov): gov for gov in EGYPT_GOVERNORATES
}

STATE_ALIAS_LOOKUP = {
    "bna swyf": "Beni Suef",
    "bny swyf": "Beni Suef",
    "mohafza alfywm": "Faiyum",
    "mhafza alfywm": "Faiyum",
    "mohafzat alfywm": "Faiyum",
    "alfywm": "Faiyum",
}

EGYPT_FIRST_NAMES = [
    "Ahmed", "Mohamed", "Mahmoud", "Omar", "Youssef", "Khaled",
    "Mostafa", "Hassan", "Hussein", "Amr", "Tarek", "Karim",
    "Alaa", "Ehab", "Sami", "Nader", "Wael", "Hany",
    "Mona", "Sara", "Aya", "Nour", "Mariam", "Salma",
    "Hala", "Doaa", "Nadia", "Rania", "Eman", "Hoda",
]

EGYPT_LAST_NAMES = [
    "El-Sayed", "Abdelrahman", "Hassan", "Ibrahim", "Mahmoud", "Kamel",
    "Mansour", "Farouk", "Saad", "Fathy", "Gamal", "Nassar",
    "Mostafa", "Ali", "Yassin", "Sherif", "Tawfik", "Rashad",
]

COUNTRY_NORMALIZE = {
    "usa": "United States", "united states": "United States",
    "unitde states": "United States", "uk": "United Kingdom",
}

_EGYPT_PHONE_RE = re.compile(r'^(\+20|002|01[0-9])')


def _is_egyptian_phone(phone):
    """Detect Egyptian phone patterns: +20x, 002x, 01xxxxxxxxx."""
    if pd.isna(phone):
        return False
    p = str(phone).strip().replace(" ", "").replace("'", "")
    return bool(_EGYPT_PHONE_RE.match(p))


def _is_egyptian_email(email):
    """Detect Egyptian email domains: .eg, .com.eg, .gov.eg, etc."""
    if pd.isna(email):
        return False
    return ".eg" in str(email).lower().split("@")[-1]


def normalize_geography(df: pd.DataFrame) -> pd.DataFrame:
    """Fix geographic inconsistencies for Egyptian contacts.

    Rules:
    1. Normalize country name variants (USA -> United States, etc.)
    2. Detect Egyptian contacts via phone or email domain
    3. If Egyptian: country -> 'Egypt', clear non-governorate state/city/postal
    4. If state is not a valid Egyptian governorate -> NULL
    """
    df = df.copy()

    # 1. Normalize country name variants
    df["country"] = df["country"].apply(
        lambda v: COUNTRY_NORMALIZE.get(str(v).strip().lower(), v) if pd.notna(v) else v
    )

    # 2. Detect Egyptian contacts
    egypt_phone = df["phone"].apply(_is_egyptian_phone)
    egypt_email = df["email"].apply(_is_egyptian_email)
    is_egyptian = egypt_phone | egypt_email

    # 3. Correct country for Egyptian contacts
    wrong_country = is_egyptian & (
        df["country"].apply(lambda v: str(v).strip().lower() if pd.notna(v) else "") != "egypt"
    )
    df.loc[wrong_country, "country"] = "Egypt"

    # 4. For Egyptian contacts: validate state against governorates
    is_egypt_now = df["country"].apply(
        lambda v: str(v).strip().lower() == "egypt" if pd.notna(v) else False
    )
    has_state = is_egypt_now & df["state"].notna()
    if has_state.any():
        df.loc[has_state, "state"] = df.loc[has_state, "state"].apply(_normalize_state_name)
        invalid_state = has_state & ~df["state"].isin(EGYPT_GOVERNORATES)
        df.loc[invalid_state, "state"] = None

    has_city = is_egypt_now & df["city"].notna()
    if has_city.any():
        df.loc[has_city, "city"] = df.loc[has_city, "city"].apply(_normalize_city_name)

    # 5. If Egypt and state missing, try to promote city when it matches a governorate
    missing_state = is_egypt_now & (df["state"].isna() | (df["state"].astype(str).str.strip() == ""))
    if missing_state.any():
        city_is_gov = missing_state & df["city"].isin(EGYPT_GOVERNORATES)
        df.loc[city_is_gov, "state"] = df.loc[city_is_gov, "city"]

    return df


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
    out["phone"]            = df.get("phone", pd.Series(dtype=str)).apply(normalize_phone)
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

    # --- geographic normalisation ---
    out = normalize_geography(out)
    out = enrich_egypt_contacts(out)

    # Egypt requires a valid governorate (state)
    is_egypt = out["country"].apply(
        lambda v: str(v).strip().lower() == "egypt" if pd.notna(v) else False
    )
    out["_dq_geo_issue"] = is_egypt & (
        out["state"].isna() | (out["state"].astype(str).str.strip() == "")
    )

    # keep DQ columns for routing
    out["_dq_severity"] = df.get("dq_issue_severity", pd.Series(dtype=str))

    # --- rejection: missing contact_id OR missing email ---
    is_rejected = out["contact_id"].isna() | out["email"].isna()

    # --- quarantine: has identity but medium / high severity ---
    is_quarantine = (~is_rejected) & (
        out["_dq_severity"].isin(["high", "med"]) | out["_dq_geo_issue"]
    )

    # --- dedup: keep first occurrence per email (fewest nulls first) ---
    out["_nulls"] = out.isnull().sum(axis=1)
    out = out.sort_values(["email", "_nulls"])
    out = out.drop_duplicates(subset=["email"], keep="first")
    # recalculate masks after dedup
    is_egypt = out["country"].apply(
        lambda v: str(v).strip().lower() == "egypt" if pd.notna(v) else False
    )
    out["_dq_geo_issue"] = is_egypt & (
        out["state"].isna() | (out["state"].astype(str).str.strip() == "")
    )
    is_rejected   = out["contact_id"].isna() | out["email"].isna()
    is_quarantine = (~is_rejected) & (
        out["_dq_severity"].isin(["high", "med"]) | out["_dq_geo_issue"]
    )

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
    out["order_status"]     = df.get("order_status", pd.Series(dtype=str)).apply(normalize_order_status)
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
