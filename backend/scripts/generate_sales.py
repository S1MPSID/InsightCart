import pandas as pd
import numpy as np
import random

customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
dates = pd.read_csv("dates.csv")

sales = []

NUM_SALES = 100000

for i in range(NUM_SALES):

    customer_id = random.randint(1, len(customers))
    product_id = random.randint(1, len(products))
    date_id = random.randint(1, len(dates))

    quantity = random.randint(1, 5)

    product = products.iloc[product_id - 1]

    selling_price = product["selling_price"]
    cost_price = product["cost_price"]

    sales_amount = quantity * selling_price
    profit = quantity * (selling_price - cost_price)

    sales.append({
        "customer_id": customer_id,
        "product_id": product_id,
        "date_id": date_id,
        "quantity": quantity,
        "sales_amount": round(sales_amount, 2),
        "profit": round(profit, 2)
    })

df = pd.DataFrame(sales)

df.to_csv("sales.csv", index=False)

print(f"{NUM_SALES} sales records generated")