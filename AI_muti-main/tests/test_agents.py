"""
tests/test_agents.py
Unit tests cho SupervisorAgent, ForecastAgent, AnomalyAgent
"""
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def monthly_df():
    from src.data_pipeline.create_sample_data import generate_dataset
    from src.data_pipeline.preprocessor import DataPreprocessor
    import tempfile, os
    raw = generate_dataset(600)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        raw.to_csv(f.name, index=False)
        tmp = f.name
    _, monthly = DataPreprocessor(tmp).run()
    os.unlink(tmp)
    return monthly


@pytest.fixture(scope="session")
def built_forecast_agent(monthly_df, tmp_path_factory):
    from src.agents.forecast_agent import ForecastAgent
    from src.data_pipeline.event_simulator import create_events_json
    db  = str(tmp_path_factory.mktemp("vdb"))
    evp = str(tmp_path_factory.mktemp("ev") / "events.json")
    create_events_json(evp)
    agent = ForecastAgent(monthly_df, vector_db_path=db, events_path=evp)
    # Build index trước
    agent.retriever.build_index(monthly_df, window=6, save=True)
    return agent, monthly_df


# ── SupervisorAgent ───────────────────────────────────────────────────────────
class TestSupervisorAgent:
    def setup_method(self):
        from src.agents.supervisor_agent import SupervisorAgent
        self.agent = SupervisorAgent()

    def test_parse_returns_dict(self):
        result = self.agent.parse("forecast furniture november 2017")
        assert isinstance(result, dict)
        for key in ["intent", "category", "year", "month", "raw_query"]:
            assert key in result

    def test_detect_forecast_intent(self):
        from src.agents.supervisor_agent import Intent
        task = self.agent.parse("What will furniture sales be next month?")
        assert task["intent"] == Intent.FORECAST

    def test_detect_anomaly_intent(self):
        from src.agents.supervisor_agent import Intent
        task = self.agent.parse("Are there any unusual spikes in the data?")
        assert task["intent"] == Intent.ANOMALY

    def test_detect_furniture_category(self):
        task = self.agent.parse("forecast furniture sales")
        assert task["category"] == "Furniture"

    def test_detect_technology_category(self):
        task = self.agent.parse("technology anomaly detection")
        assert task["category"] == "Technology"

    def test_detect_office_category(self):
        task = self.agent.parse("office supplies trend")
        assert task["category"] == "Office Supplies"

    def test_detect_year(self):
        task = self.agent.parse("sales in 2016")
        assert task["year"] == 2016

    def test_detect_english_month(self):
        task = self.agent.parse("forecast november 2017")
        assert task["month"] == 11

    def test_detect_vietnamese_month_11(self):
        task = self.agent.parse("dự báo tháng 11 2017")
        assert task["month"] == 11

    def test_detect_vietnamese_month_12(self):
        task = self.agent.parse("doanh số tháng 12")
        assert task["month"] == 12

    def test_vietnamese_month_not_confused(self):
        """tháng 12 không bị parse thành tháng 1."""
        task = self.agent.parse("tháng 12 có gì lạ không")
        assert task["month"] == 12

    def test_default_category(self):
        task = self.agent.parse("what will sales be?")
        assert task["category"] == "Furniture"  # default

    def test_describe_task(self):
        task = self.agent.parse("forecast furniture november 2017")
        desc = self.agent.describe_task(task)
        assert "forecast" in desc.lower()
        assert "Furniture" in desc

    def test_vietnamese_query_full(self):
        from src.agents.supervisor_agent import Intent
        task = self.agent.parse("Dự báo doanh số nội thất tháng 11 2017")
        assert task["intent"] == Intent.FORECAST
        assert task["category"] == "Furniture"
        assert task["month"] == 11
        assert task["year"] == 2017


# ── ForecastAgent ─────────────────────────────────────────────────────────────
class TestForecastAgent:
    def test_run_returns_dict(self, built_forecast_agent):
        agent, monthly = built_forecast_agent
        result = agent.run("Furniture", 2017, 11, top_k=2)
        assert isinstance(result, dict)

    def test_result_has_required_keys(self, built_forecast_agent):
        agent, monthly = built_forecast_agent
        result = agent.run("Technology", 2016, 6, top_k=2)
        for key in ["forecast_sales", "confidence", "forecast_range",
                    "key_drivers", "risks", "recommendation", "period"]:
            assert key in result, f"Missing key: {key}"

    def test_forecast_positive(self, built_forecast_agent):
        agent, _ = built_forecast_agent
        result = agent.run("Furniture", 2017, 11, top_k=2)
        assert result["forecast_sales"] > 0

    def test_confidence_in_range(self, built_forecast_agent):
        agent, _ = built_forecast_agent
        result = agent.run("Office Supplies", 2017, 9, top_k=2)
        assert 0 <= result["confidence"] <= 1

    def test_retrieved_patterns_attached(self, built_forecast_agent):
        agent, _ = built_forecast_agent
        result = agent.run("Furniture", 2017, 11, top_k=2)
        assert "retrieved_patterns" in result
        assert isinstance(result["retrieved_patterns"], list)

    def test_context_attached(self, built_forecast_agent):
        agent, _ = built_forecast_agent
        result = agent.run("Technology", 2016, 12, top_k=2)
        assert "context" in result
        assert len(result["context"]) > 50

    def test_all_categories_work(self, built_forecast_agent):
        agent, _ = built_forecast_agent
        for cat in ["Furniture", "Technology", "Office Supplies"]:
            result = agent.run(cat, 2017, 6, top_k=2)
            assert result["forecast_sales"] > 0


# ── AnomalyAgent ──────────────────────────────────────────────────────────────
class TestAnomalyAgent:
    def test_detect_returns_list(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent = AnomalyAgent(monthly_df)
        result = agent.detect("Furniture")
        assert isinstance(result, list)

    def test_anomaly_structure(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent     = AnomalyAgent(monthly_df)
        anomalies = agent.detect("Furniture", z_threshold=1.0)  # low threshold → more results
        if anomalies:
            a = anomalies[0]
            for key in ["yearmonth", "year", "month", "sales", "z_score", "type", "severity"]:
                assert key in a, f"Missing key: {key}"

    def test_anomaly_type_valid(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent     = AnomalyAgent(monthly_df)
        anomalies = agent.detect("Technology", z_threshold=1.0)
        for a in anomalies:
            assert a["type"] in ("spike", "dip")

    def test_anomaly_severity_valid(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent     = AnomalyAgent(monthly_df)
        anomalies = agent.detect("Office Supplies", z_threshold=1.0)
        for a in anomalies:
            assert a["severity"] in ("warning", "critical")

    def test_high_threshold_fewer_anomalies(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent = AnomalyAgent(monthly_df)
        low   = agent.detect("Furniture", z_threshold=1.0)
        high  = agent.detect("Furniture", z_threshold=3.0)
        assert len(high) <= len(low)

    def test_sorted_by_z_score(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent     = AnomalyAgent(monthly_df)
        anomalies = agent.detect("Technology", z_threshold=1.0)
        if len(anomalies) >= 2:
            z_scores = [abs(a["z_score"]) for a in anomalies]
            assert z_scores == sorted(z_scores, reverse=True)

    def test_all_categories(self, monthly_df):
        from src.agents.forecast_agent import AnomalyAgent
        agent = AnomalyAgent(monthly_df)
        for cat in ["Furniture", "Technology", "Office Supplies"]:
            result = agent.detect(cat)
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])