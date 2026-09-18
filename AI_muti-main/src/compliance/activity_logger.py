"""
src/compliance/activity_logger.py
Logs all AI decisions for audit trail (Luật AI 2025 compliance).
Each entry is a JSON line in logs/audit.jsonl.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


class ActivityLogger:
    """Write structured JSON logs for every AI decision."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.jsonl"

    def log(
        self,
        user_id: str,
        action: str,
        input_query: str,
        output_summary: str,
        confidence: float,
        category: str = "",
        period: str = "",
        reasoning_type: str = "rule_based",
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "user_id": user_id,
            "action": action,
            "input": input_query,
            "output": output_summary,
            "confidence": confidence,
            "category": category,
            "period": period,
            "reasoning_type": reasoning_type,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_logs(self, last_n: int = 20) -> list:
        if not self.log_file.exists():
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [json.loads(line) for line in lines[-last_n:]]

    def clear_logs(self) -> None:
        """Truncate the audit log (use with caution in production)."""
        if self.log_file.exists():
            self.log_file.write_text("")
            print(f"🗑️  Cleared audit log: {self.log_file}")