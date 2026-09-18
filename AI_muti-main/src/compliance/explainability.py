"""
src/compliance/explainability.py
Giải thích quyết định AI — Luật AI 2025 yêu cầu explainability
"""
from datetime import datetime, timezone


class ExplainabilityEngine:
    """Tạo giải thích ngôn ngữ tự nhiên cho mọi quyết định AI."""

    MONTH_VI = ["", "tháng 1", "tháng 2", "tháng 3", "tháng 4",
                "tháng 5", "tháng 6", "tháng 7", "tháng 8",
                "tháng 9", "tháng 10", "tháng 11", "tháng 12"]
    CAT_VI   = {
        "Furniture": "Nội thất",
        "Technology": "Công nghệ",
        "Office Supplies": "Văn phòng phẩm",
    }

    def explain_forecast(self, analysis: dict) -> str:
        """Tạo giải thích đầy đủ cho kết quả dự báo."""
        r        = analysis
        cat_vi   = self.CAT_VI.get(r["period"].split("—")[0].strip(), r["period"])
        conf_txt = ("cao" if r["confidence"] >= 0.8
                    else "thấp" if r["confidence"] < 0.7 else "trung bình")

        drivers_txt = ""
        for i, d in enumerate(r.get("key_drivers", []), 1):
            drivers_txt += f"  {i}. {d}\n"

        risks_txt = ""
        for risk in r.get("risks", []):
            risks_txt += f"  - {risk}\n"
        if not risks_txt:
            risks_txt = "  Không phát hiện rủi ro đáng kể.\n"

        return (
            f"=== GIẢI THÍCH QUYẾT ĐỊNH AI ===\n"
            f"Kỳ phân tích : {r['period']}\n"
            f"Dự báo       : ${r['forecast_sales']:,}\n"
            f"Khoảng       : ${r['forecast_range']['low']:,} – ${r['forecast_range']['high']:,}\n"
            f"Độ tin cậy   : {r['confidence']:.0%} ({conf_txt})\n"
            f"\nLý do dự báo này:\n{drivers_txt}"
            f"\nRủi ro cần lưu ý:\n{risks_txt}"
            f"\nKhuyến nghị hành động:\n"
            f"  {r['recommendation']} (điều chỉnh tồn kho: {r['stock_adjustment']})\n"
            f"\nPhương pháp: {r['reasoning_type']}\n"
            f"Thời điểm  : {r.get('generated_at', datetime.now(timezone.utc).isoformat())}\n"
            f"{'='*35}"
        )

    def explain_anomaly(self, anomaly: dict) -> str:
        """Tạo giải thích cho một điểm bất thường."""
        type_vi = "tăng đột biến" if anomaly["type"] == "spike" else "sụt giảm bất thường"
        sev_vi  = "nghiêm trọng" if anomaly["severity"] == "critical" else "cảnh báo"
        return (
            f"Tháng {anomaly['yearmonth']} ghi nhận {type_vi} "
            f"với mức độ {sev_vi}. "
            f"Doanh số ${anomaly['sales']:,.0f} lệch {abs(anomaly['z_score']):.1f} "
            f"độ lệch chuẩn so với trung bình lịch sử."
        )

    def generate_decision_card(self, analysis: dict, user_id: str = "system") -> dict:
        """Tạo decision card đầy đủ để lưu audit."""
        return {
            "decision_id":   f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "user_id":       user_id,
            "timestamp":     datetime.now(timezone.utc).isoformat() + "Z",
            "period":        analysis.get("period", ""),
            "forecast":      analysis.get("forecast_sales", 0),
            "confidence":    analysis.get("confidence", 0),
            "explanation":   self.explain_forecast(analysis),
            "drivers_count": len(analysis.get("key_drivers", [])),
            "risks_count":   len(analysis.get("risks", [])),
            "recommendation":analysis.get("recommendation", ""),
            "method":        analysis.get("reasoning_type", "rule_based"),
            "explainable":   True,
        }


if __name__ == "__main__":
    engine = ExplainabilityEngine()
    sample = {
        "period": "Furniture — Nov 2017",
        "forecast_sales": 34829,
        "confidence": 0.80,
        "forecast_range": {"low": 29604, "high": 40053},
        "key_drivers": [
            "Historical similar periods averaged $32,289",
            "Black Friday / Christmas — demand boost expected",
        ],
        "risks": ["Unusually high MoM change (+46.8%) — may revert to mean"],
        "recommendation": "MODERATE STOCK INCREASE",
        "stock_adjustment": "+5–10%",
        "reasoning_type": "rule_based_expert_system",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    print(engine.explain_forecast(sample))
    card = engine.generate_decision_card(sample, "demo_user")
    print(f"\nDecision ID: {card['decision_id']}")
    print(f"Explainable: {card['explainable']}")