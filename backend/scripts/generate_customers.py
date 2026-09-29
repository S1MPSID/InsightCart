from faker import Faker
import pandas as pd
import random

fake = Faker("en_IN")

customers = []

for i in range(10000):
    customers.append({
        "customer_name": fake.name(),
        "gender": random.choice(["Male", "Female"]),
        "age": random.randint(18, 70),
        "city": fake.city(),
        "state": fake.state(),
        "join_date": fake.date_between(start_date="-5y", end_date="today")
    })

df = pd.DataFrame(customers)

df.to_csv("customers.csv", index=False)

print("10,000 customers generated")