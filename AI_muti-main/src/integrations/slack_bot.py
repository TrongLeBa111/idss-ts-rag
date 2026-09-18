"""
src/integrations/slack_bot.py
IDSS Slack Bot — Tích hợp Slack với TS-RAG pipeline
Chạy: python src/integrations/slack_bot.py

Yêu cầu trong .env:
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_SIGNING_SECRET=...
  SLACK_PORT=3000 (tuỳ chọn)
"""
import os, sys, json, logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("idss-slack")

# ── Lazy-load pipeline components (tránh import nặng khi không cần) ──────────
_monthly_df = None
_forecast_agent = None
_anomaly_agent  = None
_supervisor     = None


def _get_components():
    """Khởi tạo pipeline components lần đầu."""
    global _monthly_df, _forecast_agent, _anomaly_agent, _supervisor

    if _monthly_df is not None:
        return _monthly_df, _forecast_agent, _anomaly_agent, _supervisor

    logger.info("⚡ Khởi tạo IDSS pipeline components...")

    from src.data_pipeline.preprocessor import DataPreprocessor
    from src.agents.forecast_agent import ForecastAgent, AnomalyAgent
    from src.agents.supervisor_agent import SupervisorAgent

    raw = Path("data/raw/superstore_sales.csv")
    if not raw.exists():
        logger.warning("⚠️  Dataset chưa tồn tại — tạo mới...")
        from src.data_pipeline.create_sample_data import generate_dataset
        raw.parent.mkdir(parents=True, exist_ok=True)
        generate_dataset(9425).to_csv(raw, index=False)

    _, _monthly_df = DataPreprocessor(
        str(raw),
        "data/processed/superstore_sales_cleaned.csv"
    ).run()

    _forecast_agent = ForecastAgent(
        monthly_df=_monthly_df,
        vector_db_path="data/vector_db",
        events_path="data/processed/events_context.json",
    )
    _anomaly_agent  = AnomalyAgent(_monthly_df)
    _supervisor     = SupervisorAgent()

    logger.info("✅ Pipeline sẵn sàng")
    return _monthly_df, _forecast_agent, _anomaly_agent, _supervisor


# ── Formatters ────────────────────────────────────────────────────────────────
def _format_forecast(analysis: dict) -> str:
    """Định dạng kết quả forecast thành Slack message đẹp."""
    r = analysis
    conf      = r["confidence"]
    conf_icon = "🟢" if conf >= 0.8 else "🔴" if conf < 0.7 else "🟡"
    drivers   = "\n".join(f"   • {d}" for d in r["key_drivers"][:3]) or "   • Không có yếu tố nổi bật"
    risks     = "\n".join(f"   ⚠️ {risk}" for risk in r["risks"][:2])

    msg = (
        f"📊 *Báo cáo Dự báo Doanh số*\n"
        f"{'─'*40}\n"
        f"*Kỳ:* {r['period']}\n"
        f"*Dự báo:* `${r['forecast_sales']:,}`\n"
        f"*Khoảng:* ${r['forecast_range']['low']:,} – ${r['forecast_range']['high']:,}\n"
        f"*Độ tin cậy:* {conf_icon} {conf:.0%}\n\n"
        f"*Yếu tố thúc đẩy:*\n{drivers}\n"
    )
    if risks:
        msg += f"\n*Rủi ro:*\n{risks}\n"
    msg += (
        f"\n💡 *Khuyến nghị:* {r['recommendation']}\n"
        f"   Điều chỉnh tồn kho: *{r['stock_adjustment']}*\n"
        f"\n_Phương pháp: {r['reasoning_type'].replace('_', ' ')}_"
    )
    return msg


def _format_anomaly(anomalies: list, category: str) -> str:
    """Định dạng kết quả anomaly detection."""
    cat_vi = {"Furniture": "Nội thất", "Technology": "Công nghệ", "Office Supplies": "Văn phòng phẩm"}
    cat_name = cat_vi.get(category, category)

    if not anomalies:
        return f"✅ *Không phát hiện bất thường* trong danh mục *{cat_name}* (Z ≥ 1.8)"

    n_critical = sum(1 for a in anomalies if a["severity"] == "critical")
    lines = [
        f"🚨 *Phát hiện {len(anomalies)} điểm bất thường — {cat_name}*",
        f"{'─'*40}",
        f"Nghiêm trọng: *{n_critical}* &nbsp;|&nbsp; Cảnh báo: *{len(anomalies) - n_critical}*\n",
    ]
    for a in anomalies[:5]:
        icon = "📈" if a["type"] == "spike" else "📉"
        sev  = "🔴 Nghiêm trọng" if a["severity"] == "critical" else "🟡 Cảnh báo"
        lines.append(
            f"{icon} *{a['yearmonth']}* — ${a['sales']:,.0f}"
            f"   |   Z={a['z_score']:+.2f}   |   {sev}"
        )
    if len(anomalies) > 5:
        lines.append(f"_...và {len(anomalies)-5} điểm khác_")
    return "\n".join(lines)


def _format_help() -> str:
    return """📚 *IDSS Bot — Hướng dẫn sử dụng*
─────────────────────────────
*Dự báo doanh số:*
  `/forecast furniture november 2017`
  `/forecast technology december 2017`
  `@idss dự báo nội thất tháng 11`

*Phát hiện bất thường:*
  `/anomaly furniture`
  `/anomaly technology`
  `@idss bất thường văn phòng phẩm`

*Câu hỏi tự nhiên:*
  `Doanh số tháng tới sẽ thế nào?`
  `Có gì bất thường trong dữ liệu không?`
  `Tại sao doanh số tháng 8 thấp?`

_Hệ thống hỗ trợ cả tiếng Anh và tiếng Việt_ 🇻🇳"""


def _log_decision(user_id: str, action: str, query: str, output: str, confidence: float):
    """Ghi audit log."""
    from src.compliance.activity_logger import ActivityLogger
    ActivityLogger("logs").log(
        user_id=user_id, action=action,
        input_query=query, output_summary=output[:200],
        confidence=confidence, reasoning_type="rule_based_expert_system",
    )


# ── Main Bot ──────────────────────────────────────────────────────────────────
def run_bot():
    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
    except ImportError:
        logger.error("❌ slack-bolt chưa được cài. Chạy: pip install slack-bolt")
        return

    SLACK_BOT_TOKEN      = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_APP_TOKEN      = os.getenv("SLACK_APP_TOKEN")  # cho Socket Mode

    if not SLACK_BOT_TOKEN or not SLACK_SIGNING_SECRET:
        logger.error("❌ Thiếu SLACK_BOT_TOKEN hoặc SLACK_SIGNING_SECRET trong .env")
        return

    app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

    # ── /forecast command ──────────────────────────────────────────────────
    @app.command("/forecast")
    def handle_forecast(ack, command, say):
        ack()
        user_id = command["user_id"]
        text    = command.get("text", "").strip() or "furniture november 2017"
        say(f"⏳ Đang chạy TS-RAG pipeline cho: `{text}`...")

        try:
            _, forecast_agent, _, supervisor = _get_components()
            task     = supervisor.parse(f"forecast {text}")
            analysis = forecast_agent.run(task["category"], task["year"], task["month"])
            msg      = _format_forecast(analysis)
            say(msg)
            _log_decision(user_id, "slack_forecast", text, msg, analysis["confidence"])
        except Exception as e:
            logger.exception(e)
            say(f"❌ Lỗi khi dự báo: `{e}`\nThử lại với: `/forecast furniture november 2017`")

    # ── /anomaly command ───────────────────────────────────────────────────
    @app.command("/anomaly")
    def handle_anomaly(ack, command, say):
        ack()
        user_id = command["user_id"]
        text    = command.get("text", "furniture").strip()

        CAT_MAP = {
            "furniture": "Furniture", "nội thất": "Furniture",
            "technology": "Technology", "tech": "Technology", "công nghệ": "Technology",
            "office": "Office Supplies", "văn phòng": "Office Supplies",
        }
        category = CAT_MAP.get(text.lower(), "Furniture")
        say(f"🔍 Đang phân tích bất thường cho *{category}*...")

        try:
            _, _, anomaly_agent, _ = _get_components()
            anomalies = anomaly_agent.detect(category, z_threshold=1.8)
            msg       = _format_anomaly(anomalies, category)
            say(msg)
            _log_decision(user_id, "slack_anomaly", text, msg, 0.85)
        except Exception as e:
            logger.exception(e)
            say(f"❌ Lỗi: `{e}`")

    # ── /idss help ────────────────────────────────────────────────────────
    @app.command("/idss")
    def handle_idss(ack, command, say):
        ack()
        text = command.get("text", "").strip().lower()
        if not text or text == "help":
            say(_format_help())
        else:
            # Route to appropriate handler
            _handle_natural_language(command["user_id"], text, say)

    # ── Mention & natural language ────────────────────────────────────────
    @app.event("app_mention")
    def handle_mention(event, say):
        user_id = event.get("user", "unknown")
        text    = event.get("text", "")
        # Remove bot mention tag
        import re
        text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
        if not text:
            say(_format_help())
            return
        _handle_natural_language(user_id, text, say)

    @app.message("dự báo|forecast|predict")
    def handle_forecast_message(message, say):
        _handle_natural_language(message["user"], message["text"], say)

    @app.message("bất thường|anomaly|unusual|spike")
    def handle_anomaly_message(message, say):
        _handle_natural_language(message["user"], message["text"], say)

    def _handle_natural_language(user_id: str, query: str, say):
        """Xử lý câu hỏi tự nhiên bằng SupervisorAgent."""
        say(f"🤔 Đang phân tích: `{query[:80]}`...")
        try:
            _, forecast_agent, anomaly_agent, supervisor = _get_components()
            task = supervisor.parse(query)
            logger.info(f"Parsed task: {supervisor.describe_task(task)}")

            from src.agents.supervisor_agent import Intent
            if task["intent"] == Intent.ANOMALY:
                anomalies = anomaly_agent.detect(task["category"], z_threshold=1.8)
                msg       = _format_anomaly(anomalies, task["category"])
                confidence = 0.85
            else:
                analysis  = forecast_agent.run(task["category"], task["year"], task["month"])
                msg       = _format_forecast(analysis)
                confidence = analysis["confidence"]

            say(msg)
            _log_decision(user_id, f"slack_{task['intent'].value}", query, msg, confidence)

        except Exception as e:
            logger.exception(e)
            say(f"❌ Xin lỗi, không thể xử lý yêu cầu: `{e}`\nGõ `/idss help` để xem hướng dẫn.")

    # ── Start bot ─────────────────────────────────────────────────────────
    logger.info("🚀 IDSS Slack Bot đang khởi động...")

    if SLACK_APP_TOKEN:
        # Socket Mode (không cần public URL)
        logger.info("📡 Chế độ: Socket Mode")
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    else:
        # HTTP Mode
        port = int(os.getenv("SLACK_PORT", 3000))
        logger.info(f"🌐 Chế độ: HTTP Mode — http://localhost:{port}")
        app.start(port=port)


if __name__ == "__main__":
    run_bot()