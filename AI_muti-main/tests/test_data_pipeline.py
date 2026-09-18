"""
tests/test_data_pipeline.py
Unit tests for Phase 1 deliverables:
  - Data loading & validation
  - Preprocessing & feature engineering
  - Event simulation
  - Monthly series structure
"""
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ======================================================================
# Fixtures
# ======================================================================
@pytest.fixture(scope="session")
def raw_df():
    """Generate raw dataset once for all tests."""
    from src.data_pipeline.create_sample_data import generate_dataset
    return generate_dataset(500)  # small subset for speed


@pytest.fixture(scope="session")
def raw_csv(tmp_path_factory, raw_df):
    """Save raw df to temp CSV and return path."""
    p = tmp_path_factory.mktemp("data") / "superstore_sales.csv"
    raw_df.to_csv(p, index=False)
    return str(p)


@pytest.fixture(scope="session")
def processed(raw_csv, tmp_path_factory):
    """Run preprocessor and return (df_clean, monthly_df)."""
    from src.data_pipeline.preprocessor import DataPreprocessor
    out = tmp_path_factory.mktemp("processed") / "cleaned.csv"
    proc = DataPreprocessor(raw_csv, str(out))
    return proc.run()


# ======================================================================
# 1. create_sample_data
# ======================================================================
class TestCreateSampleData:
    def test_shape(self, raw_df):
        assert len(raw_df) == 500
        assert raw_df.shape[1] == 20, f"Expected 20 columns, got {raw_df.shape[1]}"

    def test_required_columns(self, raw_df):
        required = ["Order ID", "Order Date", "Sales", "Profit",
                    "Category", "Region", "Quantity", "Discount"]
        for col in required:
            assert col in raw_df.columns, f"Missing column: {col}"

    def test_categories(self, raw_df):
        cats = set(raw_df["Category"].unique())
        assert cats == {"Furniture", "Technology", "Office Supplies"}

    def test_sales_positive(self, raw_df):
        assert (raw_df["Sales"] > 0).all(), "All sales should be positive"

    def test_date_range(self, raw_df):
        dates = pd.to_datetime(raw_df["Order Date"])
        assert dates.min().year >= 2014
        assert dates.max().year <= 2017

    def test_no_null_order_id(self, raw_df):
        assert raw_df["Order ID"].isnull().sum() == 0


# ======================================================================
# 2. loader
# ======================================================================
class TestLoader:
    def test_load_csv_success(self, raw_csv):
        from src.data_pipeline.loader import load_csv
        df = load_csv(raw_csv)
        assert len(df) == 500

    def test_load_csv_not_found(self):
        from src.data_pipeline.loader import load_csv
        with pytest.raises(FileNotFoundError):
            load_csv("data/raw/nonexistent.csv")

    def test_validate_data_passes(self, raw_csv):
        from src.data_pipeline.loader import load_csv, validate_data
        df = load_csv(raw_csv)
        assert validate_data(df) is True

    def test_validate_missing_column(self, raw_df):
        from src.data_pipeline.loader import validate_data
        bad_df = raw_df.drop(columns=["Sales"])
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_data(bad_df)

    def test_validate_empty_df(self):
        from src.data_pipeline.loader import validate_data
        with pytest.raises(ValueError):
            validate_data(pd.DataFrame())


# ======================================================================
# 3. preprocessor
# ======================================================================
class TestPreprocessor:
    def test_no_nulls(self, processed):
        df_clean, _ = processed
        assert df_clean.isnull().sum().sum() == 0, "Cleaned df has NaN values"

    def test_time_features_exist(self, processed):
        df_clean, _ = processed
        for col in ["Year", "Month", "Quarter", "DayOfWeek", "IsWeekend", "LeadTime"]:
            assert col in df_clean.columns, f"Missing feature: {col}"

    def test_sales_features_exist(self, processed):
        df_clean, _ = processed
        for col in ["ProfitMargin", "RevenuePerUnit", "DiscountedSales"]:
            assert col in df_clean.columns, f"Missing feature: {col}"

    def test_categorical_encoding(self, processed):
        df_clean, _ = processed
        for col in ["Segment_Code", "Region_Code", "Ship Mode_Code"]:
            assert col in df_clean.columns, f"Missing encoded column: {col}"

    def test_month_range(self, processed):
        df_clean, _ = processed
        assert df_clean["Month"].between(1, 12).all()

    def test_lead_time_non_negative(self, processed):
        df_clean, _ = processed
        assert (df_clean["LeadTime"] >= 0).all()

    def test_profit_margin_range(self, processed):
        df_clean, _ = processed
        # After clipping, ProfitMargin should be in reasonable range
        assert df_clean["ProfitMargin"].between(-2, 2).all()

    def test_monthly_series_structure(self, processed):
        _, monthly = processed
        for col in ["Year", "Month", "Category", "TotalSales",
                    "TotalProfit", "OrderCount", "YearMonth"]:
            assert col in monthly.columns, f"Missing column in monthly: {col}"

    def test_monthly_series_all_categories(self, processed):
        _, monthly = processed
        cats = set(monthly["Category"].unique())
        assert "Furniture" in cats
        assert "Technology" in cats
        assert "Office Supplies" in cats

    def test_monthly_series_sorted(self, processed):
        _, monthly = processed
        diffs = monthly["YearMonth"].diff().dropna()
        assert (diffs >= pd.Timedelta(0)).all(), "Monthly series not sorted"

    def test_total_sales_positive(self, processed):
        _, monthly = processed
        assert (monthly["TotalSales"] > 0).all()


# ======================================================================
# 4. event_simulator
# ======================================================================
class TestEventSimulator:
    def test_create_events_json(self, tmp_path):
        from src.data_pipeline.event_simulator import create_events_json
        out = str(tmp_path / "events.json")
        events = create_events_json(out)
        assert len(events) >= 20
        assert Path(out).exists()

    def test_events_json_structure(self, tmp_path):
        from src.data_pipeline.event_simulator import create_events_json
        out = str(tmp_path / "events2.json")
        events = create_events_json(out)
        for ev in events:
            assert "date" in ev
            assert "event_type" in ev
            assert "description" in ev
            assert "impact" in ev

    def test_get_events_near_date_november(self):
        from src.data_pipeline.event_simulator import get_events_near_date
        events = get_events_near_date("2017-11-01", window_days=30)
        # Black Friday is always in November
        assert len(events) > 0
        descriptions = " ".join(e["description"] for e in events).upper()
        assert "BLACK FRIDAY" in descriptions or "HOLIDAY" in descriptions

    def test_get_events_near_date_empty(self):
        from src.data_pipeline.event_simulator import get_events_near_date
        events = get_events_near_date("2017-03-15", window_days=5)
        # Very narrow window — may be empty, just check it returns a list
        assert isinstance(events, list)

    def test_events_date_format(self):
        from src.data_pipeline.event_simulator import EVENTS
        from datetime import datetime
        for ev in EVENTS:
            datetime.strptime(ev["date"], "%Y-%m-%d")  # must not raise


# ======================================================================
# Run
# ======================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
