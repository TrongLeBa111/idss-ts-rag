"""
tests/test_compliance.py
Unit tests cho ActivityLogger, RiskAssessor, ExplainabilityEngine
"""
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

SAMPLE_ANALYSIS = {
    "period": "Furniture — Nov 2017",
    "forecast_sales": 34829,
    "confidence": 0.80,
    "forecast_range": {"low": 29604, "high": 40053},
    "key_drivers": [
        "Historical similar periods averaged $32,289",
        "Black Friday / Christmas — demand boost expected",
    ],
    "risks": ["Unusually high MoM change (+46.8%)"],
    "recommendation": "MODERATE STOCK INCREASE",
    "stock_adjustment": "+5–10%",
    "reasoning_type": "rule_based_expert_system",
    "generated_at": datetime.now(timezone.utc).isoformat(),
}


# ── ActivityLogger ────────────────────────────────────────────────────────────
class TestActivityLogger:
    def test_log_creates_file(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logger.log("user1", "forecast", "query", "output", 0.8)
        assert (tmp_path / "logs" / "audit.jsonl").exists()

    def test_log_entry_structure(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logger.log("u1", "forecast_request", "input q", "output s", 0.85,
                   category="Furniture", period="Nov 2017")
        logs = logger.read_logs()
        assert len(logs) == 1
        entry = logs[0]
        for key in ["timestamp", "user_id", "action", "input", "output", "confidence"]:
            assert key in entry

    def test_log_multiple_entries(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        for i in range(5):
            logger.log(f"user{i}", "forecast", f"q{i}", f"out{i}", 0.7 + i * 0.05)
        logs = logger.read_logs()
        assert len(logs) == 5

    def test_read_logs_last_n(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        for i in range(10):
            logger.log("u", "action", f"q{i}", f"o{i}", 0.8)
        logs = logger.read_logs(last_n=3)
        assert len(logs) == 3

    def test_confidence_stored_correctly(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logger.log("u", "test", "q", "o", 0.92)
        logs = logger.read_logs()
        assert abs(logs[0]["confidence"] - 0.92) < 0.001

    def test_read_empty_log(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logs = logger.read_logs()
        assert logs == []

    def test_clear_logs(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logger.log("u", "a", "q", "o", 0.8)
        logger.clear_logs()
        assert logger.read_logs() == []

    def test_unicode_support(self, tmp_path):
        from src.compliance.activity_logger import ActivityLogger
        logger = ActivityLogger(str(tmp_path / "logs"))
        logger.log("u", "dự báo", "doanh số tháng 11", "Nội thất — $34,829", 0.8)
        logs = logger.read_logs()
        assert "tháng 11" in logs[0]["input"]


# ── RiskAssessor ──────────────────────────────────────────────────────────────
class TestRiskAssessor:
    def test_assess_returns_dict(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        assert isinstance(result, dict)

    def test_assess_required_keys(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        for key in ["system", "assessed_at", "overall_risk", "score", "criteria", "compliant"]:
            assert key in result

    def test_overall_risk_valid(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        assert result["overall_risk"] in ("LOW", "MEDIUM", "HIGH")

    def test_idss_is_low_risk(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        assert result["overall_risk"] == "LOW"

    def test_compliant_true(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        assert result["compliant"] is True

    def test_criteria_not_empty(self):
        from src.compliance.risk_assessor import RiskAssessor
        result = RiskAssessor().assess()
        assert len(result["criteria"]) >= 5

    def test_generate_report_creates_file(self, tmp_path):
        from src.compliance.risk_assessor import RiskAssessor
        out = str(tmp_path / "report.md")
        RiskAssessor().generate_report(out)
        assert Path(out).exists()
        content = Path(out).read_text(encoding="utf-8")
        assert "Luật AI" in content
        assert "Tuân thủ" in content or "MEDIUM" in content or "LOW" in content


# ── ExplainabilityEngine ──────────────────────────────────────────────────────
class TestExplainabilityEngine:
    def test_explain_forecast_returns_string(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng = ExplainabilityEngine()
        result = eng.explain_forecast(SAMPLE_ANALYSIS)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_explain_contains_forecast_value(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng    = ExplainabilityEngine()
        result = eng.explain_forecast(SAMPLE_ANALYSIS)
        assert "34,829" in result

    def test_explain_contains_recommendation(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng    = ExplainabilityEngine()
        result = eng.explain_forecast(SAMPLE_ANALYSIS)
        assert "MODERATE STOCK INCREASE" in result

    def test_explain_contains_confidence(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng    = ExplainabilityEngine()
        result = eng.explain_forecast(SAMPLE_ANALYSIS)
        assert "80%" in result

    def test_explain_anomaly_spike(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng = ExplainabilityEngine()
        a   = {"yearmonth": "2017-11", "type": "spike",
               "severity": "warning", "sales": 45000, "z_score": 2.3}
        result = eng.explain_anomaly(a)
        assert "tăng đột biến" in result
        assert "2017-11" in result

    def test_explain_anomaly_dip(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng = ExplainabilityEngine()
        a   = {"yearmonth": "2017-08", "type": "dip",
               "severity": "critical", "sales": 8000, "z_score": -3.1}
        result = eng.explain_anomaly(a)
        assert "sụt giảm" in result

    def test_decision_card_structure(self):
        from src.compliance.explainability import ExplainabilityEngine
        eng  = ExplainabilityEngine()
        card = eng.generate_decision_card(SAMPLE_ANALYSIS, "test_user")
        for key in ["decision_id", "user_id", "timestamp",
                    "forecast", "confidence", "explanation", "explainable"]:
            assert key in card

    def test_decision_card_explainable_true(self):
        from src.compliance.explainability import ExplainabilityEngine
        card = ExplainabilityEngine().generate_decision_card(SAMPLE_ANALYSIS)
        assert card["explainable"] is True

    def test_decision_id_format(self):
        from src.compliance.explainability import ExplainabilityEngine
        card = ExplainabilityEngine().generate_decision_card(SAMPLE_ANALYSIS)
        assert card["decision_id"].startswith("DEC-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])