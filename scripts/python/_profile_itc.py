import pandas as pd

df = pd.read_csv("data/raw/ITC CRM_dataset_combined.csv")
grouped = df[["customer_customer_id", "customer_contact_id"]].drop_duplicates()
dup = grouped[grouped.duplicated(subset=["customer_contact_id"], keep=False)]

print("Unique customers:", grouped["customer_customer_id"].nunique())
print("Unique contacts referenced:", grouped["customer_contact_id"].nunique())
print("Customers sharing a contact_id:", len(dup))
print()
print("Top contacts shared by multiple customers:")
print(grouped["customer_contact_id"].value_counts().head(10))
