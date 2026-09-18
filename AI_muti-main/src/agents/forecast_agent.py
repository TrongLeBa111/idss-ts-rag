"""
src/agents/forecast_agent.py
ForecastAgent  — orchestrates the full RAG pipeline for a given (category, year, month).
AnomalyAgent   — Z-score based anomaly detection on monthly sales.
"""
import numpy as np
import pandas as pd

from src.ts_rag_engine.retriever import TimeSeriesRetriever
from src.ts_rag_engine.context_augmentor import ContextAugmentor
from src.ts_rag_engine.llm_reasoner import LLMReasoner


# ======================================================================
# ForecastAgent
# ======================================================================
class ForecastAgent:
    """
    Orchestrates: Retriever → ContextAugmentor → LLMReasoner
    and returns a rich analysis dict ready for reporting / logging.
    """

    def __init__(
        self,
        monthly_df: pd.DataFrame,
        vector_db_path: str = "data/vector_db",
        events_path: str = "data/processed/events_context.json",
    ):
        self.monthly_df = monthly_df
        self.retriever = TimeSeriesRetriever(vector_db_path)
        self.augmentor = ContextAugmentor(events_path)
        self.reasoner = LLMReasoner()

    # ------------------------------------------------------------------
    def _get_current_stats(self, category: str, year: int, month: int) -> dict:
        """Compute basic stats for the target period from monthly_df."""
        cat_df = self.monthly_df[self.monthly_df["Category"] == category].sort_values("YearMonth")

        mask = (cat_df["Year"] == year) & (cat_df["Month"] == month)
        row = cat_df[mask]

        if row.empty:
            return {}

        total_sales = float(row["TotalSales"].iloc[0])
        order_count = int(row["OrderCount"].iloc[0])

        # Month-over-month change
        pos = cat_df.index.get_loc(cat_df[mask].index[0])
        if pos > 0:
            prev_sales = float(cat_df.iloc[pos - 1]["TotalSales"])
            mom_change = (total_sales - prev_sales) / (prev_sales + 1e-9) * 100
        else:
            mom_change = 0.0

        # 6-month rolling average
        start = max(0, pos - 5)
        avg_monthly = float(cat_df.iloc[start: pos + 1]["TotalSales"].mean())

        return {
            "total_sales": total_sales,
            "avg_monthly": avg_monthly,
            "mom_change_pct": round(mom_change, 1),
            "order_count": order_count,
        }

    # ------------------------------------------------------------------
    def run(
        self,
        category: str,
        year: int,
        month: int,
        top_k: int = 3,
        window: int = 6,
    ) -> dict:
        """
        Full pipeline:
          1. Retrieve top-k similar historical periods
          2. Augment with business events
          3. Reason over context → structured forecast

        Returns the analysis dict (ready for logging / dashboard).
        """
        print(f"\n🔍 Forecasting: {category} {year}-{month:02d}")

        # Step 1 — Retrieve
        patterns = self.retriever.retrieve(
            self.monthly_df, category, year, month,
            top_k=top_k, window=window,
        )
        print(f"   Retrieved {len(patterns)} similar historical patterns")

        # Step 2 — Current stats
        current_stats = self._get_current_stats(category, year, month)

        # Step 3 — Augment
        context = self.augmentor.augment(
            retrieved_patterns=patterns,
            category=category,
            year=year,
            month=month,
            current_sales_stats=current_stats if current_stats else None,
        )

        # Step 4 — Reason
        analysis = self.reasoner.reason(context, category, year, month)

        # Attach raw data for logging / dashboard
        analysis["retrieved_patterns"] = patterns
        analysis["context"] = context
        analysis["current_stats"] = current_stats

        return analysis


# ======================================================================
# AnomalyAgent
# ======================================================================
class AnomalyAgent:
    """
    Detects anomalous months in the monthly sales time series
    using Z-score thresholding. Works offline, no ML library needed.
    """

    def __init__(self, monthly_df: pd.DataFrame):
        self.monthly_df = monthly_df

    def detect(
        self,
        category: str,
        z_threshold: float = 2.0,
        min_periods: int = 6,
    ) -> list:
        """
        Return a list of anomalous months for the given category.

        Each anomaly dict contains:
          - yearmonth, year, month, sales, z_score, type, severity
        """
        cat_df = (
            self.monthly_df[self.monthly_df["Category"] == category]
            .sort_values("YearMonth")
            .copy()
        )

        if len(cat_df) < min_periods:
            print(f"⚠️  Not enough data for {category} anomaly detection ({len(cat_df)} periods)")
            return []

        sales = cat_df["TotalSales"].values
        mean = np.mean(sales)
        std = np.std(sales)

        if std < 1e-9:
            return []

        anomalies = []
        for i, row in enumerate(cat_df.itertuples()):
            z = (row.TotalSales - mean) / std
            if abs(z) >= z_threshold:
                anomalies.append({
                    "yearmonth": str(row.YearMonth)[:7],
                    "year": int(row.Year),
                    "month": int(row.Month),
                    "sales": float(row.TotalSales),
                    "z_score": round(float(z), 2),
                    "type": "spike" if z > 0 else "dip",
                    "severity": "critical" if abs(z) >= 3.0 else "warning",
                    "category": category,
                })

        return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)


# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from src.data_pipeline.preprocessor import DataPreprocessor
    from src.data_pipeline.event_simulator import create_events_json

    # Build data
    _, monthly = DataPreprocessor(
        "data/raw/superstore_sales.csv",
        "data/processed/superstore_sales_cleaned.csv",
    ).run()
    create_events_json("data/processed/events_context.json")

    # Build FAISS index
    retriever = TimeSeriesRetriever("data/vector_db")
    retriever.build_index(monthly, window=6, save=True)

    # ForecastAgent demo
    agent = ForecastAgent(
        monthly_df=monthly,
        vector_db_path="data/vector_db",
        events_path="data/processed/events_context.json",
    )
    analysis = agent.run("Furniture", 2017, 11, top_k=3)
    from src.ts_rag_engine.llm_reasoner import LLMReasoner
    print(LLMReasoner().format_report(analysis))

    # AnomalyAgent demo
    print("\n" + "=" * 50)
    anomaly_agent = AnomalyAgent(monthly)
    for cat in ["Furniture", "Technology", "Office Supplies"]:
        anomalies = anomaly_agent.detect(cat, z_threshold=1.8)
        print(f"\n{cat}: {len(anomalies)} anomalies detected")
        for a in anomalies[:3]:
            print(f"  [{a['severity'].upper()}] {a['yearmonth']}: "
                  f"${a['sales']:,.0f} (Z={a['z_score']:+.2f}, {a['type']})")
