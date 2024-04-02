import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import json

# Load the Online Retail dataset
data = pd.read_excel('Online Retail.xlsx')

# Preprocessing: Remove rows with missing or invalid InvoiceNo
data.dropna(subset=['InvoiceNo'], inplace=True)  # Remove rows with missing InvoiceNo
data['InvoiceNo'] = data['InvoiceNo'].astype(str)  # Convert InvoiceNo to string type
data = data[~data['InvoiceNo'].str.startswith('C')]  # Remove rows with InvoiceNo starting with 'C' (cancellations)

# Convert the dataset to transaction format
transactions = data.groupby(['InvoiceNo', 'Description'])['Quantity'].sum().unstack().reset_index().fillna(0).set_index('InvoiceNo')

# Convert transaction data to binary format (0/1 encoding)
def encode_units(x):
    if x <= 0:
        return 0
    if x >= 1:
        return 1
basket_sets = transactions.applymap(encode_units)

# Apply Apriori algorithm to find frequent itemsets
frequent_itemsets = apriori(basket_sets, min_support=0.03, use_colnames=True)

# Generate association rules
rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=0.6)

# Convert association rules to a format that is JSON serializable
association_rules_list = []
for index, row in rules.iterrows():
    rule_dict = {
        'antecedents': list(row['antecedents']),
        'consequents': list(row['consequents']),
        'support': row['support'],
        'confidence': row['confidence'],
        'lift': row['lift']
    }
    association_rules_list.append(rule_dict)

# Save association rules to a JSON file
with open('association_rules.json', 'w') as f:
    json.dump(association_rules_list, f)
