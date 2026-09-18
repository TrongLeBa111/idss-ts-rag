"""
src/data_pipeline/event_simulator.py
Generate realistic business events for context augmentation.
23 events spanning 2014–2017: seasonal, macro, competitor, supply chain.
"""
import json
from pathlib import Path


EVENTS = [
    # 2014
    {"date": "2014-11-28", "event_type": "seasonal", "impact": "high",
     "description": "Black Friday — peak retail demand"},
    {"date": "2014-12-25", "event_type": "holiday", "impact": "high",
     "description": "Christmas — gift purchases surge"},
    {"date": "2014-07-04", "event_type": "holiday", "impact": "medium",
     "description": "Independence Day — outdoor furniture demand up"},

    # 2015
    {"date": "2015-01-05", "event_type": "macro", "impact": "medium",
     "description": "Post-holiday inventory clearance sales"},
    {"date": "2015-04-15", "event_type": "competitor_action", "impact": "medium",
     "description": "Competitor launched 30% discount campaign"},
    {"date": "2015-06-20", "event_type": "product_launch", "impact": "high",
     "description": "New tech product line launch — 20% demand spike"},
    {"date": "2015-09-08", "event_type": "supply_chain", "impact": "negative",
     "description": "Port congestion — 2 week shipping delay"},
    {"date": "2015-11-27", "event_type": "seasonal", "impact": "high",
     "description": "Black Friday — strongest retail day of year"},
    {"date": "2015-12-25", "event_type": "holiday", "impact": "high",
     "description": "Christmas holiday season peak"},

    # 2016
    {"date": "2016-02-08", "event_type": "macro", "impact": "medium",
     "description": "Chinese New Year — furniture exports delayed"},
    {"date": "2016-05-01", "event_type": "seasonal", "impact": "medium",
     "description": "Spring refresh — office furniture demand up 15%"},
    {"date": "2016-08-01", "event_type": "macro", "impact": "low",
     "description": "Back-to-school season — office supplies peak"},
    {"date": "2016-09-01", "event_type": "competitor_action", "impact": "negative",
     "description": "New competitor entered West region market"},
    {"date": "2016-11-25", "event_type": "seasonal", "impact": "high",
     "description": "Black Friday & Cyber Monday combined campaign"},
    {"date": "2016-12-25", "event_type": "holiday", "impact": "high",
     "description": "Christmas — technology gifting trend strong"},

    # 2017
    {"date": "2017-01-01", "event_type": "macro", "impact": "medium",
     "description": "New fiscal year — corporate budget refresh"},
    {"date": "2017-03-15", "event_type": "product_launch", "impact": "high",
     "description": "Premium furniture line launched — +25% ASP"},
    {"date": "2017-05-20", "event_type": "macro", "impact": "positive",
     "description": "Economic growth report — consumer confidence up"},
    {"date": "2017-07-11", "event_type": "supply_chain", "impact": "negative",
     "description": "Supplier factory shutdown — stock shortage"},
    {"date": "2017-09-01", "event_type": "seasonal", "impact": "medium",
     "description": "Fall season — office refurbishment projects start"},
    {"date": "2017-11-01", "event_type": "seasonal", "impact": "high",
     "description": "Holiday shopping season begins — 6-week window"},
    {"date": "2017-11-24", "event_type": "seasonal", "impact": "high",
     "description": "Black Friday — highest revenue day projected"},
    {"date": "2017-12-25", "event_type": "holiday", "impact": "high",
     "description": "Christmas — technology & furniture peak demand"},
]


def create_events_json(output_path: str = "data/processed/events_context.json") -> list:
    """Dump the events list to a JSON file and return it."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(EVENTS, f, ensure_ascii=False, indent=2)
    print(f"✅ Created {len(EVENTS)} business events → {output_path}")
    return EVENTS


def get_events_near_date(date_str: str, window_days: int = 45) -> list:
    """Return events within ±window_days of given date (cross-year seasonal match)."""
    from datetime import datetime
    target = datetime.strptime(date_str[:10], "%Y-%m-%d")
    results = []
    for ev in EVENTS:
        ev_date = datetime.strptime(ev["date"], "%Y-%m-%d")
        ev_same_year = ev_date.replace(year=target.year)
        if abs((ev_same_year - target).days) <= window_days:
            results.append({**ev, "days_away": (ev_same_year - target).days})
    return sorted(results, key=lambda x: abs(x["days_away"]))


if __name__ == "__main__":
    create_events_json()
    print("\nEvents near Nov 2017:")
    for ev in get_events_near_date("2017-11-01", window_days=30):
        print(f"  [{ev['impact'].upper()}] {ev['date']}: {ev['description']}")
