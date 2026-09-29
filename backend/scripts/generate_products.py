import pandas as pd
import random

categories = {
    "Electronics": ["Laptop", "Headphones", "Smartphone"],
    "Fashion": ["T-Shirt", "Jeans", "Sneakers"],
    "Home": ["Chair", "Table", "Lamp"]
}

brands = [
    "Samsung",
    "Apple",
    "Nike",
    "Puma",
    "IKEA",
    "Sony"
]

products = []

for i in range(1000):
    category = random.choice(list(categories.keys()))
    product = random.choice(categories[category])

    cost = random.randint(100, 5000)
    selling = round(cost * random.uniform(1.2, 2.0), 2)

    products.append({
        "product_name": product,
        "category": category,
        "brand": random.choice(brands),
        "cost_price": cost,
        "selling_price": selling
    })

pd.DataFrame(products).to_csv("products.csv", index=False)

print("1000 products generated")