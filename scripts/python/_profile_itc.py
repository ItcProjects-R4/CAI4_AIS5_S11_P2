import pandas as pd, re

c = pd.read_csv("data/clean/contacts.csv")

def is_egypt_phone(p):
    if pd.isna(p): return False
    p = str(p).strip().replace(" ", "")
    return p.startswith("+20") or p.startswith("002") or bool(re.match(r"^01[0-9]{9}", p))

def is_egypt_email(e):
    if pd.isna(e): return False
    return ".eg" in str(e).lower()

egypt_phone = c["phone"].apply(is_egypt_phone)
egypt_email = c["email"].apply(is_egypt_email)
egypt_indicators = egypt_phone | egypt_email
non_egypt_country = ~c["country"].isin(["Egypt"]) | c["country"].isna()

mismatch = c[egypt_indicators & non_egypt_country]
print(f"Contacts with Egyptian phone/email but wrong country: {len(mismatch)}")
print()
print("Their countries:", mismatch["country"].value_counts().to_dict())
print()

# Also check Egyptian contacts with US states
EGYPT_GOVS = {
    "Alexandria", "Aswan", "Asyut", "Beheira", "Beni Suef", "Cairo",
    "Dakahlia", "Damietta", "Faiyum", "Gharbia", "Giza", "Ismailia",
    "Kafr El Sheikh", "Luxor", "Matrouh", "Minya", "Monufia",
    "New Valley", "North Sinai", "Port Said", "Qalyubiya", "Qena",
    "Red Sea", "Sharqia", "Sohag", "South Sinai", "Suez"
}

egypt_contacts = c[c["country"] == "Egypt"]
has_state = egypt_contacts["state"].notna()
egypt_w_state = egypt_contacts[has_state]
valid_gov = egypt_w_state["state"].isin(EGYPT_GOVS)
bad_state = egypt_w_state[~valid_gov]
print(f"Egyptian contacts with non-governorate state: {len(bad_state)}")
print("Bad states:", bad_state["state"].value_counts().head(10).to_dict())
