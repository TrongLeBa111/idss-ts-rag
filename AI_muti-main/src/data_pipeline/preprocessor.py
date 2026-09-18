"""
src/data_pipeline/preprocessor.py
Clean, transform, and feature-engineer sales data.
"""
import pandas as pd
import numpy as np
from pathlib import Path


class DataPreprocessor:
    """Clean and enrich raw sales DataFrame."""

    def __init__(self, input_path: str, output_path: str = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.input_path)
        print(f"📥 Loaded {len(df):,} rows")
        return df

    # ------------------------------------------------------------------
    # Cleaning
    # ------------------------------------------------------------------
    def _convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Order Date"] = pd.to_datetime(df["Order Date"])
        df["Ship Date"] = pd.to_datetime(df["Ship Date"])
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=["Order ID"])
        removed = before - len(df)
        if removed:
            print(f"🗑️  Removed {removed} duplicate rows")
        return df

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        cat_cols = df.select_dtypes(include=["object"]).columns
        df[cat_cols] = df[cat_cols].fillna("Unknown")
        return df

    def _clip_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Winsorize extreme Sales values at 1st–99th percentile."""
        lo = df["Sales"].quantile(0.01)
        hi = df["Sales"].quantile(0.99)
        df["Sales"] = df["Sales"].clip(lo, hi)
        return df

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Year"] = df["Order Date"].dt.year
        df["Month"] = df["Order Date"].dt.month
        df["Quarter"] = df["Order Date"].dt.quarter
        df["DayOfWeek"] = df["Order Date"].dt.dayofweek          # 0=Mon
        df["WeekOfYear"] = df["Order Date"].dt.isocalendar().week.astype(int)
        df["DayOfYear"] = df["Order Date"].dt.dayofyear
        df["IsWeekend"] = (df["DayOfWeek"] >= 5).astype(int)
        df["LeadTime"] = (df["Ship Date"] - df["Order Date"]).dt.days
        return df

    def _create_sales_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["ProfitMargin"] = np.where(
            df["Sales"] > 0, df["Profit"] / df["Sales"], 0
        )
        df["RevenuePerUnit"] = np.where(
            df["Quantity"] > 0, df["Sales"] / df["Quantity"], 0
        )
        df["DiscountedSales"] = df["Sales"] * (1 - df["Discount"])
        return df

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ordinal-encode low-cardinality columns for downstream ML."""
        mappings = {
            "Segment": {"Consumer": 0, "Corporate": 1, "Home Office": 2},
            "Region": {"West": 0, "East": 1, "Central": 2, "South": 3},
            "Ship Mode": {
                "Same Day": 0, "First Class": 1,
                "Second Class": 2, "Standard Class": 3,
            },
        }
        for col, mapping in mappings.items():
            if col in df.columns:
                df[f"{col}_Code"] = df[col].map(mapping).fillna(-1).astype(int)
        return df

    # ------------------------------------------------------------------
    # Aggregate monthly time series (needed by TS-RAG)
    # ------------------------------------------------------------------
    def _build_monthly_series(self, df: pd.DataFrame) -> pd.DataFrame:
        monthly = (
            df.groupby(["Year", "Month", "Category"])
            .agg(
                TotalSales=("Sales", "sum"),
                TotalProfit=("Profit", "sum"),
                OrderCount=("Order ID", "count"),
                AvgDiscount=("Discount", "mean"),
                AvgLeadTime=("LeadTime", "mean"),
            )
            .reset_index()
        )
        monthly["YearMonth"] = pd.to_datetime(
            monthly["Year"].astype(str) + "-" + monthly["Month"].astype(str).str.zfill(2)
        )
        monthly = monthly.sort_values("YearMonth").reset_index(drop=True)
        return monthly

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------
    def run(self) -> tuple:
        df = self.load_data()
        df = self._convert_dates(df)
        df = self._remove_duplicates(df)
        df = self._handle_missing(df)
        df = self._clip_outliers(df)
        df = self._create_time_features(df)
        df = self._create_sales_features(df)
        df = self._encode_categoricals(df)

        monthly = self._build_monthly_series(df)

        # Verify
        assert df.isnull().sum().sum() == 0, "Still has NaN values"
        assert "Month" in df.columns
        assert "ProfitMargin" in df.columns

        print(f"✅ Cleaned data: {len(df):,} rows, {len(df.columns)} columns")
        print(f"✅ Monthly series: {len(monthly)} rows")

        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.output_path, index=False)
            monthly.to_csv(
                self.output_path.parent / "monthly_sales.csv", index=False
            )
            print(f"💾 Saved → {self.output_path}")

        return df, monthly


if __name__ == "__main__":
    proc = DataPreprocessor(
        input_path="data/raw/superstore_sales.csv",
        output_path="data/processed/superstore_sales_cleaned.csv",
    )
    df, monthly = proc.run()
    print("\nSample monthly data:")
    print(monthly.tail(6).to_string(index=False))
