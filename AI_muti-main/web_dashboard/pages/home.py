"""
web_dashboard/pages/home.py — Tổng quan
"""
import json, pandas as pd, plotly.graph_objects as go
from pathlib import Path
import streamlit as st

@st.cache_data
def _load_monthly():
    p = Path("data/processed/monthly_sales.csv")
    return pd.read_csv(p, parse_dates=["YearMonth"]) if p.exists() else None

@st.cache_data
def _load_forecasts():
    p = Path("data/processed/latest_forecasts.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

CAT_COLOR = {"Furniture":"#2563EB","Technology":"#16A34A","Office Supplies":"#D97706"}
CAT_FILL  = {"Furniture":"rgba(37,99,235,0.07)","Technology":"rgba(22,163,74,0.07)","Office Supplies":"rgba(217,119,6,0.07)"}
CAT_VI    = {"Furniture":"Nội thất","Technology":"Công nghệ","Office Supplies":"Văn phòng phẩm"}

def _conf_color(c):
    return "#16A34A" if c >= 0.8 else "#DC2626" if c < 0.7 else "#D97706"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Be Vietnam Pro", color="#64748B", size=12),
    margin=dict(l=0, r=0, t=8, b=0),
)

FILTER_CSS = """
<style>
/* ── Filter Bar ── */
.filter-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 12px 16px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    margin-bottom: 20px;
}
.filter-label {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: .06em;
    white-space: nowrap;
    margin-right: 4px;
}
.filter-divider {
    width: 1px;
    height: 24px;
    background: #E2E8F0;
    margin: 0 8px;
}
.filter-btn {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    border: 1.5px solid #E2E8F0;
    background: #F8FAFC;
    color: #64748B;
    cursor: pointer;
    transition: all .15s;
    white-space: nowrap;
    line-height: 1.4;
}
.filter-btn:hover {
    border-color: #2563EB;
    color: #2563EB;
    background: #EFF6FF;
}
.filter-btn.active {
    background: #EFF6FF;
    border-color: #2563EB;
    color: #2563EB;
}

/* ── Fix text overflow trong forecast card ── */
.forecast-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    height: 100%;
    box-sizing: border-box;
    overflow: hidden;
}
.forecast-period {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.forecast-value {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.forecast-range {
    font-size: 12px;
    color: #64748B;
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.forecast-footer {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #E2E8F0;
    font-size: 12.5px;
    color: #0F172A;
    font-weight: 500;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    word-break: break-word;
}
.forecast-badge-row {
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    flex-wrap: nowrap;
    overflow: hidden;
}
.forecast-conf {
    font-size: 13px;
    font-weight: 700;
    white-space: nowrap;
    flex-shrink: 0;
}
.forecast-badge {
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
    border: 1px solid;
    flex-shrink: 0;
}
</style>
"""

def render():
    monthly   = _load_monthly()
    forecasts = _load_forecasts()

    # Inject CSS
    st.markdown(FILTER_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="page-header">
        <h1>Tổng quan Kinh doanh</h1>
        <p>Dữ liệu bán hàng 2014 – 2017 &nbsp;·&nbsp; Phân tích bằng TS-RAG Engine</p>
    </div>
    """, unsafe_allow_html=True)

    if monthly is None:
        st.warning("Chưa có dữ liệu. Chạy `python main_pipeline.py` trước.")
        return

    # ── Bộ lọc nằm ngang ────────────────────────────────────────────────────────
    all_years = sorted(monthly["YearMonth"].dt.year.unique().tolist())
    all_cats  = sorted(monthly["Category"].unique().tolist())

    if "filter_years" not in st.session_state:
        st.session_state.filter_years = set(all_years)
    if "filter_cats" not in st.session_state:
        st.session_state.filter_cats = set(all_cats)

    # Filter bar — Năm
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    st.markdown('<span class="filter-label">📅 Năm</span>', unsafe_allow_html=True)

    year_cols = st.columns([1]*len(all_years) + [0.2] + [1]*len(all_cats) + [2])
    for i, yr in enumerate(all_years):
        with year_cols[i]:
            active = yr in st.session_state.filter_years
            if st.button(
                f"{'✓ ' if active else ''}{yr}",
                key=f"yr_{yr}",
                help=f"Lọc năm {yr}",
                use_container_width=True,
            ):
                if active and len(st.session_state.filter_years) > 1:
                    st.session_state.filter_years.discard(yr)
                elif not active:
                    st.session_state.filter_years.add(yr)
                st.rerun()

    # Divider + Danh mục label
    with year_cols[len(all_years)]:
        st.markdown('<div style="display:flex;align-items:center;height:38px;"><div style="width:1px;height:24px;background:#E2E8F0;margin:auto;"></div></div>', unsafe_allow_html=True)

    st.markdown('<span class="filter-label">&nbsp;&nbsp;🏷️ Danh mục</span>', unsafe_allow_html=True)

    for j, cat in enumerate(all_cats):
        with year_cols[len(all_years) + 1 + j]:
            active_c = cat in st.session_state.filter_cats
            short_name = CAT_VI.get(cat, cat)
            if st.button(
                f"{'✓ ' if active_c else ''}{short_name}",
                key=f"cat_{cat}",
                help=f"Lọc danh mục {short_name}",
                use_container_width=True,
            ):
                if active_c and len(st.session_state.filter_cats) > 1:
                    st.session_state.filter_cats.discard(cat)
                elif not active_c:
                    st.session_state.filter_cats.add(cat)
                st.rerun()

    # Nút Reset
    with year_cols[-1]:
        if st.button("↺ Đặt lại", key="reset_filter", use_container_width=True):
            st.session_state.filter_years = set(all_years)
            st.session_state.filter_cats  = set(all_cats)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Áp dụng bộ lọc ───────────────────────────────────────────────────────────
    df = monthly[
        (monthly["YearMonth"].dt.year.isin(st.session_state.filter_years)) &
        (monthly["Category"].isin(st.session_state.filter_cats))
    ]

    if df.empty:
        st.info("Không có dữ liệu khớp với bộ lọc hiện tại.")
        return

    # KPI
    total_sales  = df["TotalSales"].sum()
    total_profit = df["TotalProfit"].sum()
    total_orders = df["OrderCount"].sum()
    margin       = total_profit / total_sales * 100 if total_sales else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng Doanh thu",  f"${total_sales:,.0f}",  f"{'–'.join(map(str, sorted(st.session_state.filter_years)))}")
    c2.metric("Tổng Lợi nhuận",  f"${total_profit:,.0f}", f"Biên {margin:.1f}%")
    c3.metric("Tổng Đơn hàng",   f"{total_orders:,}",     f"{len(st.session_state.filter_cats)} danh mục")
    c4.metric("Kỳ dữ liệu",      f"{len(df)} tháng")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Charts
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="card" style="padding-bottom:8px;">', unsafe_allow_html=True)
        st.markdown("<h2>Doanh thu theo Thời gian</h2>", unsafe_allow_html=True)
        fig = go.Figure()
        for cat in sorted(df["Category"].unique()):
            if cat not in st.session_state.filter_cats:
                continue
            sub = df[df["Category"] == cat].sort_values("YearMonth")
            fig.add_trace(go.Scatter(
                x=sub["YearMonth"], y=sub["TotalSales"],
                name=CAT_VI.get(cat, cat), mode="lines",
                line=dict(color=CAT_COLOR.get(cat, "#888"), width=2.5),
                fill="tozeroy",
                fillcolor=CAT_FILL.get(cat, "rgba(100,100,100,0.05)"),
            ))
        fig.update_layout(
            **CHART_LAYOUT, height=280,
            xaxis=dict(showgrid=False, zeroline=False, tickformat="%m/%Y", tickangle=-30, color="#94A3B8"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, tickprefix="$", color="#94A3B8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#0F172A")),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="card" style="padding-bottom:8px;">', unsafe_allow_html=True)
        st.markdown("<h2>Tỷ lệ Danh mục</h2>", unsafe_allow_html=True)
        cat_totals = df.groupby("Category")["TotalSales"].sum()
        labels_vi  = [CAT_VI.get(c, c) for c in cat_totals.index]
        colors_pie  = [CAT_COLOR.get(c, "#888") for c in cat_totals.index]
        fig2 = go.Figure(go.Pie(
            labels=labels_vi, values=cat_totals.values, hole=0.6,
            marker=dict(colors=colors_pie, line=dict(color="#FFFFFF", width=3)),
            textfont=dict(family="Be Vietnam Pro", size=12, color="#FFFFFF"),
            textinfo="percent",
        ))
        fig2.update_layout(
            **CHART_LAYOUT, height=280,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#0F172A", size=12)),
            annotations=[dict(text="Doanh thu", x=0.5, y=0.5, showarrow=False,
                              font=dict(family="Be Vietnam Pro", size=13, color="#0F172A"))],
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Forecasts
    if forecasts:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:14px;">
            <h2 style="margin-bottom:2px;">Dự báo AI mới nhất</h2>
            <p style="font-size:14px;">Kết quả từ TS-RAG Engine &nbsp;·&nbsp; Rule-based reasoning</p>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(len(forecasts))
        for col, f in zip(cols, forecasts):
            conf   = f["confidence"]
            color  = _conf_color(conf)
            bg     = "#F0FDF4" if conf >= 0.8 else "#FEF2F2" if conf < 0.7 else "#FFFBEB"
            border = "#BBF7D0" if conf >= 0.8 else "#FECACA" if conf < 0.7 else "#FDE68A"
            badge  = "Tin cậy cao" if conf >= 0.8 else "Thấp" if conf < 0.7 else "Trung bình"
            # Giới hạn recommendation trong 2 dòng
            rec_text = f["recommendation"][:80].rstrip() + ("…" if len(f["recommendation"]) > 80 else "")
            with col:
                st.markdown(f"""
                <div class="forecast-card" style="border-top:3px solid {color};">
                    <div class="forecast-period">{f["period"]}</div>
                    <div class="forecast-value" style="color:{color};">${f["forecast_sales"]:,}</div>
                    <div class="forecast-range">${f["forecast_range"]["low"]:,} – ${f["forecast_range"]["high"]:,}</div>
                    <div class="forecast-badge-row">
                        <span class="forecast-conf" style="color:{color};">{conf:.0%} tin cậy</span>
                        <span class="forecast-badge" style="background:{bg};border-color:{border};color:{color};">{badge}</span>
                    </div>
                    <div class="forecast-footer">{rec_text}</div>
                </div>
                """, unsafe_allow_html=True)