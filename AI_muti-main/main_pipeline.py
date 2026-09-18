"""
main_pipeline.py
Master script: Run the full IDSS pipeline end-to-end.
Usage: python main_pipeline.py
"""
import sys
import json
from pathlib import Path

# Fix: Windows terminal may default to cp1252 — force UTF-8 for emoji output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))


def step(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print("🚀 IDSS — Intelligent Decision Support System")
    print("   Full Pipeline: Data → RAG → Agents → Report")

    # ----------------------------------------------------------------
    # STEP 1: Generate sample data
    # ----------------------------------------------------------------
    step("STEP 1: Data Generation")
    from src.data_pipeline.create_sample_data import generate_dataset
    import pandas as pd

    raw_path = Path("data/raw/superstore_sales.csv")
    if not raw_path.exists():
        print("Generating sample dataset...")
        df = generate_dataset(9425)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_path, index=False)
    else:
        print(f"✅ Dataset already exists: {raw_path}")

    # ----------------------------------------------------------------
    # STEP 2: Preprocess
    # ----------------------------------------------------------------
    step("STEP 2: Data Preprocessing")
    from src.data_pipeline.preprocessor import DataPreprocessor

    proc = DataPreprocessor(
        input_path=str(raw_path),
        output_path="data/processed/superstore_sales_cleaned.csv",
    )
    df_clean, monthly_df = proc.run()

    # ----------------------------------------------------------------
    # STEP 3: Create events
    # ----------------------------------------------------------------
    step("STEP 3: Event Context Creation")
    from src.data_pipeline.event_simulator import create_events_json
    create_events_json("data/processed/events_context.json")

    # ----------------------------------------------------------------
    # STEP 4: Build vector index
    # ----------------------------------------------------------------
    step("STEP 4: Building Vector Index (FAISS)")
    from src.ts_rag_engine.retriever import TimeSeriesRetriever

    retriever = TimeSeriesRetriever("data/vector_db")
    retriever.build_index(monthly_df, window=6, save=True)

    # ----------------------------------------------------------------
    # STEP 5: Run Forecast Agent
    # ----------------------------------------------------------------
    step("STEP 5: Running Forecast Agent")
    from src.agents.forecast_agent import ForecastAgent, AnomalyAgent
    from src.ts_rag_engine.llm_reasoner import LLMReasoner

    agent = ForecastAgent(
        monthly_df=monthly_df,
        vector_db_path="data/vector_db",
        events_path="data/processed/events_context.json",
    )
    reasoner = LLMReasoner()

    demo_queries = [
        ("Furniture", 2017, 11),
        ("Technology", 2017, 12),
        ("Office Supplies", 2017, 9),
    ]

    results = []
    for cat, yr, mo in demo_queries:
        analysis = agent.run(cat, yr, mo, top_k=3)
        results.append(analysis)
        print(f"\n{reasoner.format_report(analysis)}")

    # ----------------------------------------------------------------
    # STEP 6: Anomaly Detection
    # ----------------------------------------------------------------
    step("STEP 6: Anomaly Detection")
    anomaly_agent = AnomalyAgent(monthly_df)
    for cat in ["Furniture", "Technology", "Office Supplies"]:
        anomalies = anomaly_agent.detect(cat, z_threshold=1.8)
        print(f"\n{cat}: {len(anomalies)} anomalies detected")
        for a in anomalies[:3]:
            print(f"  [{a['severity'].upper()}] {a['yearmonth']}: "
                  f"${a['sales']:,.0f} (Z={a['z_score']:+.2f}, {a['type']})")

    # ----------------------------------------------------------------
    # STEP 7: Compliance Logging
    # ----------------------------------------------------------------
    step("STEP 7: Compliance Logging")
    from src.compliance.activity_logger import ActivityLogger
    logger = ActivityLogger("logs")
    for analysis in results:
        logger.log(
            user_id="demo_user",
            action="forecast_request",
            input_query=f"Forecast for {analysis['period']}",
            output_summary=f"Forecast ${analysis['forecast_sales']:,}, confidence {analysis['confidence']:.0%}",
            confidence=analysis["confidence"],
            category=analysis["period"].split("—")[0].strip(),
            period=analysis["period"],
            reasoning_type=analysis["reasoning_type"],
        )
    logs = logger.read_logs(last_n=3)
    print(f"\n📋 Last {len(logs)} audit log entries:")
    for log in logs:
        print(f"  [{log['timestamp']}] {log['action']} | {log['period']} | conf={log['confidence']}")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    step("✅ PIPELINE COMPLETE")
    print(f"""
Summary:
  • Dataset: {len(df_clean):,} rows processed
  • Monthly series: {len(monthly_df)} data points
  • Vector index: {retriever.vs.total_vectors} embeddings
  • Forecasts generated: {len(results)}
  • Audit logs written: {len(results)}

Output files:
  • data/processed/superstore_sales_cleaned.csv
  • data/processed/monthly_sales.csv
  • data/processed/events_context.json
  • data/vector_db/index.faiss
  • data/vector_db/metadata.pkl
  • logs/audit.jsonl

Next steps:
  • Run: streamlit run web_dashboard/app.py
  • Run tests: pytest -v tests/
    """)

    # Save results JSON for dashboard
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    with open("data/processed/latest_forecasts.json", "w") as f:
        # Serialize (remove non-JSON-serializable fields)
        clean_results = []
        for r in results:
            clean_r = {k: v for k, v in r.items() if k not in ("retrieved_patterns", "context")}
            clean_results.append(clean_r)
        json.dump(clean_results, f, indent=2)
    print("💾 Forecasts saved → data/processed/latest_forecasts.json")


if __name__ == "__main__":
    main()