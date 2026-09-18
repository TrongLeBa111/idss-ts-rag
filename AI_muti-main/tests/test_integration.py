"""
tests/test_integrations.py
Unit tests cho MessagingGateway và SupervisorAgent routing
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── MessagingGateway ──────────────────────────────────────────────────────────
class TestSupervisorRouting:
    """Kiểm tra routing logic của SupervisorAgent với nhiều query patterns."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.agents.supervisor_agent import SupervisorAgent, Intent
        self.agent  = SupervisorAgent()
        self.Intent = Intent

    # Forecast intent
    @pytest.mark.parametrize("query", [
        "forecast furniture november 2017",
        "What will sales be next month?",
        "dự báo nội thất tháng 11",
        "predict technology december",
        "tháng tới doanh số bao nhiêu",
    ])
    def test_forecast_queries(self, query):
        task = self.agent.parse(query)
        assert task["intent"] == self.Intent.FORECAST, f"Failed for: {query}"

    # Anomaly intent
    @pytest.mark.parametrize("query", [
        "Are there any unusual spikes?",
        "anomaly detection furniture",
        "bất thường trong dữ liệu",
        "có gì lạ trong tháng này không",
        "sales drop detected",
    ])
    def test_anomaly_queries(self, query):
        task = self.agent.parse(query)
        assert task["intent"] == self.Intent.ANOMALY, f"Failed for: {query}"

    # Category detection
    @pytest.mark.parametrize("query,expected_cat", [
        ("forecast furniture sales", "Furniture"),
        ("nội thất tháng 11",        "Furniture"),
        ("technology anomaly",        "Technology"),
        ("công nghệ bất thường",      "Technology"),
        ("office supplies trend",     "Office Supplies"),
        ("văn phòng phẩm dự báo",    "Office Supplies"),
    ])
    def test_category_detection(self, query, expected_cat):
        task = self.agent.parse(query)
        assert task["category"] == expected_cat, f"Failed for: {query}"

    # Month detection — critical fix test
    @pytest.mark.parametrize("query,expected_month", [
        ("tháng 1 doanh số",   1),
        ("tháng 10 bất thường", 10),
        ("tháng 11 dự báo",    11),
        ("tháng 12 nội thất",  12),
        ("november 2017",      11),
        ("december sales",     12),
        ("january forecast",    1),
    ])
    def test_month_detection(self, query, expected_month):
        task = self.agent.parse(query)
        assert task["month"] == expected_month, \
            f"Expected {expected_month}, got {task['month']} for: {query}"

    # Year detection
    @pytest.mark.parametrize("query,expected_year", [
        ("forecast 2014", 2014),
        ("sales 2015",    2015),
        ("data 2016",     2016),
        ("2017 report",   2017),
    ])
    def test_year_detection(self, query, expected_year):
        task = self.agent.parse(query)
        assert task["year"] == expected_year

    # Full Vietnamese query
    def test_full_vietnamese_pipeline(self):
        queries = [
            ("Dự báo doanh số nội thất tháng 11 2017", "Furniture", 11, 2017),
            ("Bất thường công nghệ tháng 10",          "Technology", 10, 2017),
            ("dự báo văn phòng phẩm tháng 12 2016",   "Office Supplies", 12, 2016),
        ]
        for q, cat, month, year in queries:
            task = self.agent.parse(q)
            assert task["category"] == cat,  f"Cat failed: {q}"
            assert task["month"]    == month, f"Month failed: {q}"
            assert task["year"]     == year,  f"Year failed: {q}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])