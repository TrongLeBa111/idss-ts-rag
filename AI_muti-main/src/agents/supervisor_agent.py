"""
src/agents/supervisor_agent.py
Supervisor agent — detects intent and routes to the correct sub-agent.
No LangChain dependency needed; pure Python with keyword routing.
Supports both English and Vietnamese queries.
"""
import re
from enum import Enum


class Intent(Enum):
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    EXPLAIN = "explain"
    TREND = "trend"
    COMPARE = "compare"
    UNKNOWN = "unknown"


INTENT_PATTERNS = {
    Intent.FORECAST: [
        r"\bforecast\b", r"\bpredict\b", r"\bnext month\b", r"\bnext quarter\b",
        r"\bwill.*sales\b", r"\bexpect\b", r"\bproject\b", r"\bdự báo\b",
        r"\btháng tới\b", r"\bquý tới\b",
    ],
    Intent.ANOMALY: [
        r"\banomaly\b", r"\bannomalie\b", r"\bunusual\b", r"\bspike\b", r"\bdrop\b",
        r"\boutlier\b", r"\bstrange\b", r"\bwrong\b", r"\babnormal\b",
        r"\bbất thường\b", r"\blạ\b", r"\bnghiêm trọng\b",
    ],
    Intent.EXPLAIN: [
        r"\bwhy\b", r"\bexplain\b", r"\breason\b", r"\bcause\b", r"\bbecause\b",
        r"\bunderstand\b", r"\btại sao\b", r"\bgiải thích\b", r"\blý do\b",
    ],
    Intent.TREND: [
        r"\btrend\b", r"\bgrowing\b", r"\bdeclining\b", r"\bover time\b",
        r"\bhistory\b", r"\bhistorical\b", r"\bxu hướng\b", r"\blịch sử\b",
    ],
    Intent.COMPARE: [
        r"\bcompare\b", r"\bvs\b", r"\bversus\b", r"\bdifference\b",
        r"\bbetter\b", r"\bworse\b", r"\bso sánh\b", r"\bhơn\b",
    ],
}

CATEGORY_PATTERNS = {
    "Furniture": [r"\bfurnitur\b", r"\bchair\b", r"\btable\b", r"\bdesk\b", r"\bnội thất\b"],
    "Technology": [r"\btech\b", r"\btechnology\b", r"\bphone\b", r"\blaptop\b", r"\belectronic\b", r"\bcông nghệ\b"],
    "Office Supplies": [r"\boffice\b", r"\bsuppl\b", r"\bpaper\b", r"\bbinder\b", r"\bvăn phòng\b"],
}

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    # Vietnamese
    "tháng 1": 1, "tháng 2": 2, "tháng 3": 3, "tháng 4": 4,
    "tháng 5": 5, "tháng 6": 6, "tháng 7": 7, "tháng 8": 8,
    "tháng 9": 9, "tháng 10": 10, "tháng 11": 11, "tháng 12": 12,
}


class SupervisorAgent:
    """
    Routes user queries to the appropriate analysis action.
    Returns a structured task dict consumed by downstream agents.
    """

    DEFAULT_CATEGORY = "Furniture"
    DEFAULT_YEAR = 2017
    DEFAULT_MONTH = 11

    def parse(self, query: str) -> dict:
        """
        Parse free-text query into a structured task.

        Returns:
            {
              "intent": Intent,
              "category": str,
              "year": int,
              "month": int,
              "raw_query": str,
            }
        """
        q = query.lower()

        intent = self._detect_intent(q)
        category = self._detect_category(q)
        year, month = self._detect_period(q)

        return {
            "intent": intent,
            "category": category,
            "year": year,
            "month": month,
            "raw_query": query,
        }

    def _detect_intent(self, q: str) -> Intent:
        scores = {}
        for intent, patterns in INTENT_PATTERNS.items():
            scores[intent] = sum(1 for p in patterns if re.search(p, q))
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else Intent.FORECAST   # default: forecast

    def _detect_category(self, q: str) -> str:
        for cat, patterns in CATEGORY_PATTERNS.items():
            if any(re.search(p, q) for p in patterns):
                return cat
        return self.DEFAULT_CATEGORY

    def _detect_period(self, q: str) -> tuple:
        year = self.DEFAULT_YEAR
        month = self.DEFAULT_MONTH

        # Year: 4-digit number
        year_match = re.search(r"\b(201[4-9]|202[0-9])\b", q)
        if year_match:
            year = int(year_match.group(1))

        # Month: name or number — sort by length desc để "tháng 11" match trước "tháng 1"
        for name, num in sorted(MONTH_MAP.items(), key=lambda x: -len(x[0])):
            if name in q:
                month = num
                break
        else:
            m = re.search(r"\bmonth[:\s]+(\d{1,2})\b", q)
            if m:
                month = int(m.group(1))
            else:
                m = re.search(r"\b(\d{1,2})/(\d{4})\b", q)
                if m:
                    month, year = int(m.group(1)), int(m.group(2))

        return year, max(1, min(12, month))

    def describe_task(self, task: dict) -> str:
        return (
            f"Intent: {task['intent'].value} | "
            f"Category: {task['category']} | "
            f"Period: {task['year']}-{task['month']:02d}"
        )


# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = SupervisorAgent()

    queries = [
        "What will furniture sales be next month?",
        "Are there any unusual spikes in technology this year?",
        "Why did office supplies drop in August 2017?",
        "Show me the trend for furniture over 2017",
        "Dự báo doanh số nội thất tháng 11 2017",
        "Tại sao doanh số tháng 8 thấp vậy?",
    ]

    for q in queries:
        task = agent.parse(q)
        print(f"Q: {q}")
        print(f"→ {agent.describe_task(task)}")
        print()