"""
src/data_pipeline/create_sample_data.py
Generate realistic Superstore-like sales data for demo purposes.
No Kaggle account needed.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

CATEGORIES = {
    "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
    "Office Supplies": ["Binders", "Paper", "Storage", "Appliances", "Labels", "Pens"],
    "Technology": ["Phones", "Accessories", "Machines", "Copiers"],
}

REGIONS = ["West", "East", "Central", "South"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]


def generate_seasonal_sales(date, category):
    """Add seasonal patterns to sales."""
    month = date.month
    day_of_year = date.timetuple().tm_yday

    # Base by category
    base = {"Furniture": 400, "Office Supplies": 80, "Technology": 600}[category]

    # Seasonal multiplier (Q4 boost, summer dip)
    seasonal = 1.0 + 0.4 * np.sin((day_of_year - 60) * 2 * np.pi / 365)
    if month in [11, 12]:
        seasonal += 0.3   # Holiday boost
    if month in [7, 8]:
        seasonal -= 0.15  # Summer dip

    # Weekly pattern (weekends lower)
    weekly = 0.9 if date.weekday() >= 5 else 1.0

    # Random noise
    noise = np.random.lognormal(0, 0.3)

    return max(10, base * seasonal * weekly * noise)


def generate_dataset(n_rows: int = 9425) -> pd.DataFrame:
    """Generate a synthetic Superstore-style sales dataset."""
    start_date = datetime(2014, 1, 3)
    end_date = datetime(2017, 12, 31)
    date_range = (end_date - start_date).days

    rows = []
    order_counter = 1000

    for i in range(n_rows):
        order_date = start_date + timedelta(days=random.randint(0, date_range))
        ship_days = {
            "Standard Class": 5, "Second Class": 3,
            "First Class": 2, "Same Day": 0,
        }
        ship_mode = random.choice(SHIP_MODES)
        ship_date = order_date + timedelta(days=ship_days[ship_mode] + random.randint(0, 2))

        category = random.choice(list(CATEGORIES.keys()))
        sub_category = random.choice(CATEGORIES[category])
        region = random.choice(REGIONS)
        segment = random.choice(SEGMENTS)

        sales = generate_seasonal_sales(order_date, category)
        quantity = random.randint(1, 10)
        discount = random.choice([0, 0, 0, 0.1, 0.2, 0.3, 0.4, 0.5])
        profit = sales * random.uniform(0.05, 0.35) * (1 - discount * 1.5)

        rows.append({
            "Order ID": f"CA-{order_date.year}-{order_counter + i:06d}",
            "Order Date": order_date.strftime("%Y-%m-%d"),
            "Ship Date": ship_date.strftime("%Y-%m-%d"),
            "Ship Mode": ship_mode,
            "Customer ID": f"CG-{random.randint(10000, 20000)}",
            "Segment": segment,
            "Country": "United States",
            "City": random.choice(["Los Angeles", "New York", "Chicago", "Houston", "Phoenix"]),
            "State": random.choice(["California", "New York", "Texas", "Illinois", "Arizona"]),
            "Postal Code": random.randint(10000, 99999),
            "Region": region,
            "Product ID": f"FUR-{random.randint(100, 999)}-{random.randint(10000, 99999)}",
            "Category": category,
            "Sub-Category": sub_category,
            "Product Name": f"{sub_category} Model {random.randint(100, 999)}",
            "Sales": round(sales, 2),
            "Quantity": quantity,
            "Discount": discount,
            "Profit": round(profit, 2),
            "Year Of The Order": order_date.year,
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Order Date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    from pathlib import Path
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    print("Generating sample dataset...")
    df = generate_dataset(9425)
    df.to_csv("data/raw/superstore_sales.csv", index=False)
    print(f"✅ Created dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"   Date range: {df['Order Date'].min()} → {df['Order Date'].max()}")
    print(f"   Total Sales: ${df['Sales'].sum():,.0f}")
    print(f"   Categories: {df['Category'].unique()}")
