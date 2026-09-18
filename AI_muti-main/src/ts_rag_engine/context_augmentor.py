"""
src/ts_rag_engine/context_augmentor.py
Combine retrieved time-series patterns with external business events
to produce a rich context string for the LLM reasoner.
"""
import json
from datetime import datetime
from pathlib import Path


class ContextAugmentor:
    """
    Merges historical pattern matches with relevant business events
    to produce structured context for LLM reasoning.
    """

    def __init__(self, events_path: str = "data/processed/events_context.json"):
        self.events_path = Path(events_path)
        self.events = self._load_events()

    def _load_events(self) -> list:
        if self.events_path.exists():
            with open(self.events_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    # ------------------------------------------------------------------
    def get_relevant_events(self, year: int, month: int, window_days: int = 45) -> list:
        """Find events near the given year-month (matched across years)."""
        target = datetime(year, month, 15)  # mid-month anchor
        relevant = []
        for ev in self.events:
            try:
                ev_date = datetime.strptime(ev["date"], "%Y-%m-%d")
                ev_same_year = ev_date.replace(year=year)
                days_away = abs((ev_same_year - target).days)
                if days_away <= window_days:
                    relevant.append({**ev, "days_away": days_away})
            except (ValueError, KeyError):
                continue
        return sorted(relevant, key=lambda x: x["days_away"])

    # ------------------------------------------------------------------
    def augment(
        self,
        retrieved_patterns: list,
        category: str,
        year: int,
        month: int,
        current_sales_stats: dict = None,
    ) -> str:
        """
        Build a structured context string from:
        - Current period info
        - Retrieved similar historical patterns
        - Relevant business events
        - (Optional) current period actual stats
        """
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        month_name = month_names[month]

        lines = [
            f"=== CONTEXT FOR: {category.upper()} — {month_name} {year} ===",
            "",
        ]

        # Current period
        if current_sales_stats:
            lines += [
                "## Current Period Stats",
                f"- Total Sales: ${current_sales_stats.get('total_sales', 0):,.0f}",
                f"- Average Monthly Sales: ${current_sales_stats.get('avg_monthly', 0):,.0f}",
                f"- Month-over-Month Change: {current_sales_stats.get('mom_change_pct', 0):+.1f}%",
                f"- Order Count: {current_sales_stats.get('order_count', 0):,}",
                "",
            ]

        # Historical patterns
        lines.append("## Similar Historical Patterns Found")
        if retrieved_patterns:
            for i, pat in enumerate(retrieved_patterns, 1):
                trend_arrow = "↑" if pat.get("sales_trend_pct", 0) > 0 else "↓"
                lines.append(
                    f"{i}. {pat['yearmonth']} | "
                    f"Avg Sales: ${pat['avg_sales']:,.0f} | "
                    f"Peak: ${pat['peak_sales']:,.0f} | "
                    f"6-month trend: {trend_arrow}{abs(pat.get('sales_trend_pct', 0)):.1f}% | "
                    f"Similarity: {pat['similarity']:.1%}"
                )
            lines.append("")
        else:
            lines.append("No similar patterns found in historical data.")
            lines.append("")

        # Business events
        events = self.get_relevant_events(year, month)
        lines.append("## Relevant Business Events (±45 days)")
        if events:
            impact_emoji = {
                "high": "🔴", "medium": "🟡", "low": "🟢",
                "negative": "⚫", "positive": "🔵",
            }
            for ev in events[:5]:
                emoji = impact_emoji.get(ev.get("impact", "medium"), "⚪")
                lines.append(
                    f"- {emoji} [{ev['event_type'].upper()}] {ev['date']}: "
                    f"{ev['description']} (impact: {ev.get('impact', 'unknown')})"
                )
        else:
            lines.append("- No significant events detected near this period.")
        lines.append("")

        # Pattern summary
        if retrieved_patterns:
            avg_hist_sales = sum(p["avg_sales"] for p in retrieved_patterns) / len(retrieved_patterns)
            avg_trend = sum(p.get("sales_trend_pct", 0) for p in retrieved_patterns) / len(retrieved_patterns)
            lines += [
                "## Pattern Summary",
                f"- Historical avg sales (similar periods): ${avg_hist_sales:,.0f}",
                f"- Average 6-month trend in similar periods: {avg_trend:+.1f}%",
                f"- Number of comparable historical periods found: {len(retrieved_patterns)}",
                "",
            ]

        return "\n".join(lines)


# ------------------------------------------------------------------
if __name__ == "__main__":
    aug = ContextAugmentor("data/processed/events_context.json")

    fake_patterns = [
        {"yearmonth": "2016-11", "avg_sales": 2800.0, "peak_sales": 4200.0,
         "sales_trend_pct": 22.5, "similarity": 0.91},
        {"yearmonth": "2015-11", "avg_sales": 2550.0, "peak_sales": 3800.0,
         "sales_trend_pct": 15.3, "similarity": 0.87},
    ]

    context = aug.augment(
        retrieved_patterns=fake_patterns,
        category="Furniture",
        year=2017,
        month=11,
        current_sales_stats={
            "total_sales": 31200, "avg_monthly": 2600,
            "mom_change_pct": 18.4, "order_count": 142,
        },
    )
    print(context)
