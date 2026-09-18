"""
web_dashboard/pages/anomaly_detection.py — Phát hiện Bất thường
"""
import sys, pandas as pd, plotly.graph_objects as go
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CAT_VI    = {"Furniture":"Nội thất","Technology":"Công nghệ","Office Supplies":"Văn phòng phẩm"}
CAT_COLOR = {"Furniture":"#2563EB","Technology":"#16A34A","Office Supplies":"#D97706"}

@st.cache_data
def load_monthly():
    p = Path("data/processed/monthly_sales.csv")
    return pd.read_csv(p, parse_dates=["YearMonth"]) if p.exists() else None

def render():
    st.markdown("""
    <div class="page-header">
        <h1 style="margin:0 0 4px;">🚨 Phát hiện Bất thường</h1>
        <p style="margin:0;color:#64748B;font-size:15px;">
            Phát hiện tháng bất thường bằng Z-score · Phân loại tăng đột biến / sụt giảm
        </p>
    </div>
    """, unsafe_allow_html=True)

    monthly = load_monthly()
    if monthly is None:
        st.error("Chạy `python main_pipeline.py` trước.")
        return

    # ── Bộ lọc ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**⚙️ Cài đặt phát hiện**")
    c1, c2 = st.columns([2, 2])
    category  = c1.selectbox("Danh mục", list(CAT_VI.keys()), format_func=lambda x: CAT_VI[x])

    # 2 lựa chọn → dùng Radio thay Dropdown (theo design system)
    c2.markdown("**Mức độ nhạy**")
    sensitivity = c2.radio(
        "sensitivity", ["Tiêu chuẩn (Z ≥ 1.8)", "Chặt chẽ (Z ≥ 2.5)"],
        horizontal=True, label_visibility="collapsed",
    )
    threshold = 1.8 if "1.8" in sensitivity else 2.5
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Detect ────────────────────────────────────────────────────────────────
    from src.agents.forecast_agent import AnomalyAgent
    anomalies = AnomalyAgent(monthly).detect(category, z_threshold=threshold)

    cat_df = monthly[monthly["Category"] == category].sort_values("YearMonth")
    mean   = cat_df["TotalSales"].mean()
    std    = cat_df["TotalSales"].std()
    color  = CAT_COLOR.get(category, "#2563EB")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── KPI summary ──────────────────────────────────────────────────────────
    n_crit   = sum(1 for a in anomalies if a["severity"] == "critical")
    n_warn   = len(anomalies) - n_crit
    n_spikes = sum(1 for a in anomalies if a["type"] == "spike")
    n_dips   = sum(1 for a in anomalies if a["type"] == "dip")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng bất thường", len(anomalies))
    k2.metric("🔴 Nghiêm trọng", n_crit)
    k3.metric("📈 Tăng đột biến", n_spikes)
    k4.metric("📉 Sụt giảm",     n_dips)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="card" style="padding-bottom:4px;">', unsafe_allow_html=True)
    st.markdown(f"**📊 Biểu đồ bất thường — {CAT_VI[category]}** (ngưỡng Z ≥ {threshold})")

    fig = go.Figure()

    # Band ± threshold*std
    band_x = list(cat_df["YearMonth"]) + list(cat_df["YearMonth"])[::-1]
    band_y = ([mean + threshold*std]*len(cat_df) + [mean - threshold*std]*len(cat_df))
    fig.add_trace(go.Scatter(
        x=band_x, y=band_y, fill="toself",
        fillcolor="rgba(220,38,38,0.06)", line=dict(color="rgba(0,0,0,0)"),
        name="Vùng bất thường", showlegend=True,
    ))

    fig.add_hline(y=mean, line=dict(color="#94A3B8", width=1, dash="dot"),
                  annotation_text=f"Trung bình ${mean:,.0f}",
                  annotation_font=dict(color="#64748B", size=12))

    # Normal line
    anomaly_months = {a["yearmonth"] for a in anomalies}
    normal = cat_df[~cat_df["YearMonth"].astype(str).str[:7].isin(anomaly_months)]
    fig.add_trace(go.Scatter(
        x=normal["YearMonth"], y=normal["TotalSales"],
        name="Bình thường", mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=5, color=color),
    ))

    # Anomaly points
    for atype, acolor, sym, label in [
        ("spike", "#DC2626", "triangle-up",   "Tăng đột biến"),
        ("dip",   "#D97706", "triangle-down", "Sụt giảm"),
    ]:
        group = [a for a in anomalies if a["type"] == atype]
        if group:
            fig.add_trace(go.Scatter(
                x=pd.to_datetime([a["yearmonth"]+"-01" for a in group]),
                y=[a["sales"] for a in group],
                name=label, mode="markers",
                marker=dict(color=acolor, size=14, symbol=sym,
                            line=dict(color="#FFFFFF", width=2)),
            ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Be Vietnam Pro", color="#64748B", size=13),
        xaxis=dict(showgrid=False, zeroline=False, tickformat="%m/%Y", tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, tickprefix="$"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#0F172A"),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=40, b=0), height=320,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Danh sách bất thường ─────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if anomalies:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**📋 Danh sách {len(anomalies)} điểm bất thường phát hiện**")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        for a in anomalies:
            is_crit  = a["severity"] == "critical"
            acolor   = "#DC2626" if a["type"] == "spike" else "#D97706"
            bg       = "#FEF2F2" if is_crit else "#FFFBEB"
            border   = "#FECACA" if is_crit else "#FDE68A"
            icon     = "📈" if a["type"] == "spike" else "📉"
            sev_text = "Nghiêm trọng" if is_crit else "Cảnh báo"
            z_pct    = min(100, int(abs(a["z_score"])/4*100))

            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};
                         border-radius:10px;padding:14px 18px;margin-bottom:8px;">
                <div style="display:flex;align-items:center;justify-content:space-between;
                             flex-wrap:wrap;gap:8px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span style="font-size:24px;">{icon}</span>
                        <div>
                            <div style="font-size:16px;font-weight:700;color:#0F172A;">
                                {a["yearmonth"]}
                                <span style="font-size:13px;font-weight:400;color:#64748B;margin-left:8px;">
                                    {"Tăng đột biến" if a["type"]=="spike" else "Sụt giảm"}
                                </span>
                            </div>
                            <div style="font-size:15px;font-weight:600;color:{acolor};margin-top:2px;">
                                ${a["sales"]:,.0f}
                            </div>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:white;border:1px solid {border};
                                     border-radius:20px;padding:3px 12px;
                                     font-size:12px;font-weight:700;color:{acolor};">
                            {sev_text}
                        </span>
                        <div style="font-size:13px;color:#64748B;margin-top:6px;">
                            Z-score: <strong style="color:{acolor};">{a["z_score"]:+.2f}</strong>
                        </div>
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <div style="background:white;border-radius:4px;height:6px;">
                        <div style="background:{acolor};width:{z_pct}%;height:6px;border-radius:4px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success(f"✅ Không phát hiện bất thường nào với ngưỡng Z ≥ {threshold} cho danh mục {CAT_VI[category]}.")