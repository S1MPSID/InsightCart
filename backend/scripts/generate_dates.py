import pandas as pd

dates = pd.date_range(
    start="2022-01-01",
    end="2025-12-31"
)

df = pd.DataFrame({
    "full_date": dates
})

df["day"] = df["full_date"].dt.day
df["month"] = df["full_date"].dt.month
df["quarter"] = df["full_date"].dt.quarter
df["year"] = df["full_date"].dt.year
df["day_name"] = df["full_date"].dt.day_name()

df.to_csv("dates.csv", index=False)

print("Dates generated")