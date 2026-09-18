"""
src/data_pipeline/loader.py
Load and validate raw sales data.
"""
import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = [
    "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Segment", "Region", "Category",
    "Sub-Category", "Sales", "Quantity", "Discount", "Profit",
]


def load_csv(path: str) -> pd.DataFrame:
    """Load CSV file and return DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path)
    print(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns from {path.name}")
    return df


def validate_data(df: pd.DataFrame) -> bool:
    """Check required columns and basic integrity."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if len(df) == 0:
        raise ValueError("Dataset is empty")
    print(f"✅ Validation passed — {len(df):,} rows, all required columns present")
    return True


if __name__ == "__main__":
    df = load_csv("data/raw/superstore_sales.csv")
    validate_data(df)
    print(df.head(3).to_string())
