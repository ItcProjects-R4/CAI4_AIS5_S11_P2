import pandas as pd

# Load all clean CSVs
batch    = pd.read_csv('data/clean/etl_batch.csv')
contacts = pd.read_csv('data/clean/contacts.csv')
cust     = pd.read_csv('data/clean/customers.csv')
prod     = pd.read_csv('data/clean/products.csv')
orders   = pd.read_csv('data/clean/sales_orders.csv')
lines    = pd.read_csv('data/clean/order_lines.csv')

print('=== ROW COUNTS ===')
for name, df in [('etl_batch', batch), ('contacts', contacts), ('customers', cust),
                 ('products', prod), ('sales_orders', orders), ('order_lines', lines)]:
    print(f'  {name}: {len(df)} rows')

print()
print('=== NOT NULL VIOLATIONS ===')
c_nulls = contacts[contacts['contact_id'].isna() | contacts['email'].isna() | contacts['etl_batch_id'].isna()]
print(f'  contacts: {len(c_nulls)}')
cu_nulls = cust[cust['customer_id'].isna() | cust['contact_id'].isna() | cust['etl_batch_id'].isna()]
print(f'  customers: {len(cu_nulls)}')
p_nulls = prod[prod['product_id'].isna() | prod['sku'].isna() | prod['product_name'].isna() | prod['etl_batch_id'].isna()]
print(f'  products: {len(p_nulls)}')
o_nulls = orders[orders['order_id'].isna() | orders['customer_id'].isna() | orders['order_date'].isna() | orders['etl_batch_id'].isna()]
print(f'  sales_orders: {len(o_nulls)}')
l_nulls = lines[lines['order_line_id'].isna() | lines['order_id'].isna() | lines['product_id'].isna() | lines['line_number'].isna() | lines['quantity'].isna() | lines['unit_price'].isna()]
print(f'  order_lines: {len(l_nulls)}')

print()
print('=== UNIQUE KEY VIOLATIONS ===')
print(f'  contacts duplicate email: {contacts.duplicated(subset=["email"]).sum()}')
print(f'  customers duplicate contact_id: {cust.duplicated(subset=["contact_id"]).sum()}')
print(f'  products duplicate sku: {prod.duplicated(subset=["sku"]).sum()}')
print(f'  order_lines duplicate (order_id,line_number): {lines.duplicated(subset=["order_id","line_number"]).sum()}')

print()
print('=== FK INTEGRITY ===')
orphan_cust = cust[~cust['contact_id'].isin(contacts['contact_id'])]
print(f'  customers with orphan contact_id: {len(orphan_cust)}')
orphan_ord = orders[~orders['customer_id'].isin(cust['customer_id'])]
print(f'  sales_orders with orphan customer_id: {len(orphan_ord)}')
orphan_lines_order = lines[~lines['order_id'].isin(orders['order_id'])]
print(f'  order_lines with orphan order_id: {len(orphan_lines_order)}')
orphan_lines_prod = lines[~lines['product_id'].isin(prod['product_id'])]
print(f'  order_lines with orphan product_id: {len(orphan_lines_prod)}')

all_batch_ids = set(batch['etl_batch_id'])
for name, df in [('contacts', contacts), ('customers', cust), ('products', prod), ('sales_orders', orders)]:
    missing = df[~df['etl_batch_id'].isin(all_batch_ids)]
    print(f'  {name} with orphan etl_batch_id: {len(missing)}')

print()
print('=== CHECK CONSTRAINTS ===')
neg_price = prod[prod['list_price'].notna() & (prod['list_price'] < 0)]
print(f'  products with negative list_price: {len(neg_price)}')
neg_total = orders[orders['order_total'].notna() & (orders['order_total'] < 0)]
print(f'  sales_orders with negative order_total: {len(neg_total)}')
zero_qty = lines[lines['quantity'] <= 0]
print(f'  order_lines with quantity <= 0: {len(zero_qty)}')
neg_uprice = lines[lines['unit_price'] < 0]
print(f'  order_lines with negative unit_price: {len(neg_uprice)}')

print()
print('=== FIELD LENGTH CHECKS ===')
# contact_id VARCHAR(36)
long_ids = contacts[contacts['contact_id'].str.len() > 36]
print(f'  contacts with contact_id > 36 chars: {len(long_ids)}')
# email VARCHAR(320)
long_email = contacts[contacts['email'].str.len() > 320]
print(f'  contacts with email > 320 chars: {len(long_email)}')
# sku VARCHAR(100)
long_sku = prod[prod['sku'].str.len() > 100]
print(f'  products with sku > 100 chars: {len(long_sku)}')
# currency CHAR(3) 
if 'currency' in orders.columns:
    bad_curr = orders[orders['currency'].notna() & (orders['currency'].str.len() != 3)]
    print(f'  sales_orders with currency != 3 chars: {len(bad_curr)}')
