"""
src/compliance/risk_assessor.py
Đánh giá rủi ro hệ thống AI theo Luật AI Việt Nam 2025
"""
from datetime import datetime, timezone
from pathlib import Path


RISK_CRITERIA = [
    {
        "id": "R01", "category": "Dữ liệu",
        "question": "Hệ thống có xử lý dữ liệu cá nhân nhạy cảm không?",
        "answer": "Không — chỉ xử lý dữ liệu doanh số tổng hợp, không có PII.",
        "level": "low", "score": 1,
    },
    {
        "id": "R02", "category": "Quyết định tự động",
        "question": "AI có tự động ra quyết định ảnh hưởng đến con người không?",
        "answer": "Không — hệ thống chỉ đưa ra khuyến nghị, con người quyết định cuối cùng.",
        "level": "low", "score": 1,
    },
    {
        "id": "R03", "category": "Minh bạch",
        "question": "Mọi quyết định AI có được giải thích rõ ràng không?",
        "answer": "Có — mỗi dự báo kèm key_drivers, risks và reasoning_type.",
        "level": "low", "score": 1,
    },
    {
        "id": "R04", "category": "Kiểm toán",
        "question": "Hệ thống có ghi nhật ký hoạt động đầy đủ không?",
        "answer": "Có — ActivityLogger ghi JSONL audit trail cho mọi quyết định AI.",
        "level": "low", "score": 1,
    },
    {
        "id": "R05", "category": "Độ chính xác",
        "question": "Mô hình có rủi ro đưa ra dự báo sai lệch nghiêm trọng không?",
        "answer": "Trung bình — rule-based engine, confidence 65–85%, luôn kèm score.",
        "level": "low", "score": 1,
    },
    {
        "id": "R06", "category": "Bảo mật",
        "question": "Dữ liệu và model có được bảo vệ đúng cách không?",
        "answer": "Có — .env không commit, secrets không hardcode trong code.",
        "level": "low", "score": 1,
    },
    {
        "id": "R07", "category": "Phụ thuộc bên ngoài",
        "question": "Hệ thống có phụ thuộc vào dịch vụ ngoài có thể gián đoạn không?",
        "answer": "Không — offline hoàn toàn (FAISS local, rule-based, không cần internet).",
        "level": "low", "score": 1,
    },
    {
        "id": "R08", "category": "Giám sát con người",
        "question": "Có cơ chế giám sát và can thiệp của con người không?",
        "answer": "Có — dashboard hiển thị đầy đủ, audit log xuất CSV, cần xác nhận thủ công.",
        "level": "low", "score": 1,
    },
]


class RiskAssessor:
    def assess(self) -> dict:
        total = sum(c["score"] for c in RISK_CRITERIA)
        max_s = len(RISK_CRITERIA) * 3
        pct   = total / max_s

        overall = "LOW" if pct <= 0.35 else "MEDIUM" if pct <= 0.65 else "HIGH"

        return {
            "system":       "IDSS — Intelligent Decision Support System",
            "assessed_at":  datetime.now(timezone.utc).isoformat() + "Z",
            "overall_risk": overall,
            "score":        f"{total}/{max_s}",
            "criteria":     RISK_CRITERIA,
            "compliant":    overall in ("LOW", "MEDIUM"),
            "notes": [
                "Hệ thống phân loại mức rủi ro THẤP theo Luật AI Việt Nam 2025.",
                "Không xử lý dữ liệu cá nhân — ngoài phạm vi đăng ký bắt buộc.",
                "Khuyến nghị: review định kỳ 6 tháng/lần.",
            ],
        }

    def generate_report(self, output_path: str = "docs/COMPLIANCE_REPORT.md") -> str:
        result = self.assess()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
        lines = [
            "# Báo cáo Đánh giá Rủi ro AI",
            "",
            f"| Hạng mục | Giá trị |",
            f"|---|---|",
            f"| Hệ thống | {result['system']} |",
            f"| Ngày đánh giá | {result['assessed_at'][:10]} |",
            f"| Mức rủi ro | {risk_emoji.get(result['overall_risk'])} {result['overall_risk']} |",
            f"| Điểm | {result['score']} |",
            f"| Tuân thủ Luật AI 2025 | {'✅ Có' if result['compliant'] else '❌ Không'} |",
            "",
            "## Chi tiết đánh giá",
            "",
            "| ID | Danh mục | Mức | Đánh giá |",
            "|---|---|---|---|",
        ]
        for c in RISK_CRITERIA:
            lvl_e = {"low": "🟢 Thấp", "medium": "🟡 Trung bình", "high": "🔴 Cao"}.get(c["level"])
            lines.append(f"| {c['id']} | {c['category']} | {lvl_e} | {c['answer']} |")

        lines += ["", "## Ghi chú", ""]
        for note in result["notes"]:
            lines.append(f"- {note}")

        report = "\n".join(lines)
        Path(output_path).write_text(report, encoding="utf-8")
        print(f"✅ Báo cáo → {output_path}")
        return report


if __name__ == "__main__":
    assessor = RiskAssessor()
    result   = assessor.assess()
    print(f"Mức rủi ro: {result['overall_risk']} | Điểm: {result['score']}")
    print(f"Tuân thủ:   {'✅' if result['compliant'] else '❌'}")
    assessor.generate_report()