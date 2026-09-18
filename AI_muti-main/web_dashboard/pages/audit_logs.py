"""
web_dashboard/pages/audit_logs.py — Nhật ký Kiểm toán
"""
import json, pandas as pd
from pathlib import Path
import streamlit as st

def render():
    st.markdown("""
    <div class="page-header">
        <h1 style="margin:0 0 4px;">📋 Nhật ký Kiểm toán</h1>
        <p style="margin:0;color:#64748B;font-size:15px;">
            Tuân thủ Luật AI 2025 · Ghi nhận mọi quyết định AI · Xuất báo cáo CSV
        </p>
    </div>
    """, unsafe_allow_html=True)

    log_path = Path("logs/audit.jsonl")
    if not log_path.exists():
        st.warning("Chưa có nhật ký. Chạy `python main_pipeline.py` trước.")
        return

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    logs  = [json.loads(l) for l in lines if l.strip()]
    if not logs:
        st.info("File nhật ký trống.")
        return

    df = pd.DataFrame(logs)

    # ── KPI ─────────────────────────────────────────────────────────────────
    avg_conf = df["confidence"].mean()
    n_high   = (df["confidence"] >= 0.8).sum()
    n_low    = (df["confidence"] < 0.7).sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📊 Tổng quyết định",   len(logs))
    k2.metric("🎯 Độ tin cậy TB",     f"{avg_conf:.0%}")
    k3.metric("✅ Tin cậy cao (≥80%)", n_high)
    k4.metric("⚠️ Tin cậy thấp (<70%)", n_low)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Bộ lọc ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**🔍 Lọc nhật ký**")
    c1, c2 = st.columns([2, 2])
    filter_action = c1.selectbox("Loại hành động", ["Tất cả"] + sorted(df["action"].unique()))

    # 2 lựa chọn → Radio
    c2.markdown("**Mức độ tin cậy**")
    conf_filter = c2.radio("conf", ["Tất cả", "Chỉ cao (≥80%)"],
                           horizontal=True, label_visibility="collapsed")

    filtered = df.copy()
    if filter_action != "Tất cả":
        filtered = filtered[filtered["action"] == filter_action]
    if conf_filter == "Chỉ cao (≥80%)":
        filtered = filtered[filtered["confidence"] >= 0.8]

    st.markdown(f"""
    <div style="margin-top:8px;font-size:14px;color:#64748B;">
        Hiển thị <strong>{len(filtered)}</strong> / {len(logs)} bản ghi
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Danh sách log ────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for _, row in filtered.iloc[::-1].iterrows():
        conf  = row["confidence"]
        color = "#16A34A" if conf >= 0.8 else "#DC2626" if conf < 0.7 else "#D97706"
        bg    = "#F0FDF4" if conf >= 0.8 else "#FEF2F2" if conf < 0.7 else "#FFFBEB"
        badge = "Cao" if conf >= 0.8 else "Thấp" if conf < 0.7 else "TB"
        ts    = row["timestamp"][:19].replace("T", " ")

        st.markdown(f"""
        <div style="background:{bg};border-radius:8px;padding:14px 18px;
                     margin-bottom:8px;border-left:4px solid {color};">
            <div style="display:flex;justify-content:space-between;
                         align-items:flex-start;flex-wrap:wrap;gap:8px;">
                <div>
                    <div style="font-size:13px;color:#64748B;margin-bottom:4px;">
                        🕐 {ts} UTC &nbsp;·&nbsp;
                        <span style="background:white;border:1px solid #E2E8F0;
                                     border-radius:4px;padding:1px 8px;font-weight:600;">
                            {row["action"]}
                        </span>
                        &nbsp;·&nbsp; {row.get("period","")}
                    </div>
                    <div style="font-size:15px;color:#0F172A;font-weight:500;line-height:1.5;">
                        {row.get("output","")[:120]}
                    </div>
                    <div style="font-size:13px;color:#64748B;margin-top:4px;">
                        👤 {row.get("user_id","")} &nbsp;·&nbsp;
                        🤖 {row.get("reasoning_type","").replace("_"," ")}
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:1.4rem;font-weight:800;color:{color};">{conf:.0%}</div>
                    <span style="background:white;border:1px solid {color}33;
                                 border-radius:20px;padding:2px 10px;
                                 font-size:11px;font-weight:700;color:{color};">
                        {badge}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    csv = filtered.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇ Xuất CSV (UTF-8)",
        data=csv,
        file_name="idss_audit_logs.csv",
        mime="text/csv",
    )