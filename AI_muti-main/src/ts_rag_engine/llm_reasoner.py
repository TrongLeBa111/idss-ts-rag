"""
src/ts_rag_engine/llm_reasoner.py
Reasoning engine for sales analysis.
- Primary:  Anthropic Claude via API (if key available)
- Fallback: Rule-based expert system (fully open-source, no key needed)
"""
import os
import re
import json
from datetime import datetime


# ------------------------------------------------------------------
# Rule-based reasoner (no API needed)
# ------------------------------------------------------------------
class RuleBasedReasoner:
    """
    Expert-system reasoner that produces structured analysis
    from the augmented context. Works offline, zero cost.
    """

    SEASONAL_MONTHS = {11, 12}   # Nov, Dec
    SUMMER_MONTHS = {6, 7, 8}
    Q1_MONTHS = {1, 2, 3}

    def reason(self, context: str, category: str, year: int, month: int) -> dict:
        """
        Parse context and generate structured analysis.
        Returns a dict with forecast, drivers, risks, recommendation.
        """
        # Extract numbers from context
        avg_hist = self._extract_number(context, r"Historical avg sales.*?\$([0-9,]+)")
        avg_trend = self._extract_float(context, r"Average 6-month trend.*?([+-]?\d+\.?\d*)%")
        mom_change = self._extract_float(context, r"Month-over-Month Change:\s*([+-]?\d+\.?\d*)%")
        similarity_count = self._extract_number(context, r"(\d+) comparable historical")
        current_sales = self._extract_number(context, r"Total Sales:\s*\$([0-9,]+)")

        # Event signals
        has_holiday = "BLACK FRIDAY" in context.upper() or "CHRISTMAS" in context.upper()
        has_competitor = "COMPETITOR" in context.upper()
        has_supply_issue = "SUPPLY_CHAIN" in context.upper() or "SHORTAGE" in context.upper()
        has_product_launch = "PRODUCT_LAUNCH" in context.upper()

        # Forecast
        base_forecast = avg_hist if avg_hist else (current_sales or 2000)
        seasonal_multiplier = 1.0

        if month in self.SEASONAL_MONTHS:
            seasonal_multiplier += 0.20
        elif month in self.SUMMER_MONTHS:
            seasonal_multiplier -= 0.10
        elif month in self.Q1_MONTHS:
            seasonal_multiplier -= 0.05

        if has_holiday:
            seasonal_multiplier += 0.15
        if has_product_launch:
            seasonal_multiplier += 0.10
        if has_competitor:
            seasonal_multiplier -= 0.08
        if has_supply_issue:
            seasonal_multiplier -= 0.12

        trend_adj = 1 + (avg_trend or 0) / 100 * 0.5   # weight trend at 50%
        forecast = base_forecast * seasonal_multiplier * trend_adj

        # Confidence
        confidence = 0.75
        if similarity_count and similarity_count >= 3:
            confidence += 0.10
        if has_holiday:
            confidence += 0.05
        if has_supply_issue:
            confidence -= 0.10
        confidence = round(min(max(confidence, 0.4), 0.95), 2)

        # Drivers
        drivers = []
        if avg_hist:
            drivers.append(
                f"Historical similar periods averaged ${avg_hist:,.0f} — strong baseline signal"
            )
        if avg_trend and avg_trend > 0:
            drivers.append(f"Positive {avg_trend:.1f}% trend in comparable historical windows")
        if has_holiday:
            drivers.append("High-impact seasonal event detected (Black Friday / Christmas) — demand boost expected")
        if has_product_launch:
            drivers.append("New product launch in period — incremental demand driver")
        if month in self.SEASONAL_MONTHS:
            drivers.append(f"Month {month} is historically a peak retail period")

        # Risks
        risks = []
        if has_competitor:
            risks.append("Competitor promotional activity detected — potential market share pressure")
        if has_supply_issue:
            risks.append("Supply chain disruption flagged — stock availability risk")
        if mom_change and abs(mom_change) > 25:
            risks.append(f"Unusually high MoM change ({mom_change:+.1f}%) — may revert to mean")
        if not drivers:
            risks.append("Limited historical signal — forecast reliability lower than usual")

        # Recommendation
        if forecast > (base_forecast * 1.15):
            action = "INCREASE STOCK — forecast significantly above baseline"
            stock_adj = "+15–20%"
        elif forecast > (base_forecast * 1.05):
            action = "MODERATE STOCK INCREASE — forecast slightly above baseline"
            stock_adj = "+5–10%"
        elif forecast < (base_forecast * 0.90):
            action = "REDUCE PROCUREMENT — forecast below historical average"
            stock_adj = "-10–15%"
        else:
            action = "MAINTAIN CURRENT LEVELS — forecast inline with historical"
            stock_adj = "0–5%"

        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        return {
            "period": f"{category} — {month_names[month]} {year}",
            "forecast_sales": round(forecast),
            "confidence": confidence,
            "forecast_range": {
                "low": round(forecast * 0.85),
                "high": round(forecast * 1.15),
            },
            "key_drivers": drivers,
            "risks": risks,
            "recommendation": action,
            "stock_adjustment": stock_adj,
            "reasoning_type": "rule_based_expert_system",
            "generated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _extract_number(text: str, pattern: str):
        m = re.search(pattern, text)
        if m:
            return float(m.group(1).replace(",", ""))
        return None

    @staticmethod
    def _extract_float(text: str, pattern: str):
        m = re.search(pattern, text)
        if m:
            return float(m.group(1))
        return None

    def format_report(self, analysis: dict) -> str:
        """Pretty-print the analysis dict as a human-readable report."""
        r = analysis
        lines = [
            "📊 SALES ANALYSIS REPORT",
            "=" * 50,
            f"Period:     {r['period']}",
            f"Forecast:   ${r['forecast_sales']:,}",
            f"Range:      ${r['forecast_range']['low']:,} – ${r['forecast_range']['high']:,}",
            f"Confidence: {r['confidence']:.0%}",
            "",
            "🔍 KEY DRIVERS",
        ]
        for d in r["key_drivers"]:
            lines.append(f"  ✅ {d}")
        if r["risks"]:
            lines.append("\n⚠️  RISKS")
            for risk in r["risks"]:
                lines.append(f"  ⚠️  {risk}")
        lines += [
            "",
            "💡 RECOMMENDATION",
            f"  Action:          {r['recommendation']}",
            f"  Stock Adjustment: {r['stock_adjustment']}",
            "",
            f"[Method: {r['reasoning_type']}]",
        ]
        return "\n".join(lines)


# ------------------------------------------------------------------
# LLM Reasoner facade (auto-selects backend)
# ------------------------------------------------------------------
class LLMReasoner:
    """
    Facade that tries Claude API first, falls back to rule-based.
    For this open-source setup: always uses RuleBasedReasoner.
    """

    def __init__(self, use_api: bool = False):
        self._rule_based = RuleBasedReasoner()
        self._use_api = use_api and bool(os.getenv("ANTHROPIC_API_KEY"))

    def reason(self, context: str, category: str, year: int, month: int) -> dict:
        """Main entry point — returns structured analysis dict."""
        return self._rule_based.reason(context, category, year, month)

    def format_report(self, analysis: dict) -> str:
        return self._rule_based.format_report(analysis)


# ------------------------------------------------------------------
if __name__ == "__main__":
    context = """
=== CONTEXT FOR: FURNITURE — November 2017 ===

## Current Period Stats
- Total Sales: $31,200
- Average Monthly Sales: $2,600
- Month-over-Month Change: +18.4%
- Order Count: 142

## Similar Historical Patterns Found
1. 2016-11 | Avg Sales: $2,800 | Peak: $4,200 | 6-month trend: ↑22.5% | Similarity: 91.0%
2. 2015-11 | Avg Sales: $2,550 | Peak: $3,800 | 6-month trend: ↑15.3% | Similarity: 87.0%

## Relevant Business Events (±45 days)
- 🔴 [SEASONAL] 2017-11-24: Black Friday — highest revenue day projected (impact: high)
- 🔴 [SEASONAL] 2017-11-01: Holiday shopping season begins (impact: high)
- 🔴 [HOLIDAY] 2017-12-25: Christmas — technology & furniture peak demand (impact: high)

## Pattern Summary
- Historical avg sales (similar periods): $2,675
- Average 6-month trend in similar periods: +18.9%
- Number of comparable historical periods found: 2
"""

    reasoner = LLMReasoner()
    analysis = reasoner.reason(context, "Furniture", 2017, 11)
    print(reasoner.format_report(analysis))
    print(f"\nJSON output:\n{json.dumps(analysis, indent=2)}")
