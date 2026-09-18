"""
web_dashboard/pages/forecast_analysis.py — Phân tích Dự báo
"""
import sys, pandas as pd, plotly.graph_objects as go
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CAT_COLOR = {"Furniture": "#2563EB", "Technology": "#16A34A", "Office Supplies": "#D97706"}
CAT_FILL  = {"Furniture": "rgba(37,99,235,0.08)", "Technology": "rgba(22,163,74,0.08)", "Office Supplies": "rgba(217,119,6,0.08)"}
CAT_VI    = {"Furniture": "Nội thất", "Technology": "Công nghệ", "Office Supplies": "Văn phòng phẩm"}
MONTH_VI  = ["","Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
             "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]

@st.cache_data
def load_data():
    p = Path("data/processed/monthly_sales.csv")
    return pd.read_csv(p, parse_dates=["YearMonth"]) if p.exists() else None

def run_forecast(category, year, month):
    from src.ts_rag_engine.retriever import TimeSeriesRetriever
    from src.ts_rag_engine.context_augmentor import ContextAugmentor
    from src.ts_rag_engine.llm_reasoner import LLMReasoner

    monthly = load_data()
    retriever = TimeSeriesRetriever("data/vector_db")
    try:
        retriever.load_index()
    except Exception:
        retriever.build_index(monthly, window=6, save=True)

    patterns = retriever.retrieve(monthly, category, year, month, top_k=3)
    augmentor = ContextAugmentor("data/processed/events_context.json")

    mask = (monthly["Category"] == category) & (monthly["Year"] == year) & (monthly["Month"] == month)
    row = monthly[mask]
    stats = {}
    if not row.empty:
        sales = float(row["TotalSales"].iloc[0])
        cat_df = monthly[monthly["Category"] == category].sort_values("YearMonth")
        pos = cat_df.index.get_loc(cat_df[mask].index[0])
        prev = float(cat_df.iloc[pos-1]["TotalSales"]) if pos > 0 else sales
        stats = {"total_sales": sales, "avg_monthly": sales,
                 "mom_change_pct": round((sales-prev)/(prev+1e-9)*100,1),
                 "order_count": int(row["OrderCount"].iloc[0])}

    context  = augmentor.augment(patterns, category, year, month, stats or None)
    reasoner = LLMReasoner()
    analysis = reasoner.reason(context, category, year, month)
    analysis["retrieved_patterns"] = patterns
    analysis["context"] = context
    return analysis

def render():
    st.markdown("""
    <div class="page-header">
        <h1 style="margin:0 0 4px;">📈 Phân tích Dự báo</h1>
        <p style="margin:0;color:#64748B;font-size:15px;">
            Truy xuất mẫu lịch sử → Làm giàu ngữ cảnh → Suy luận AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    monthly = load_data()
    if monthly is None:
        st.error("Chạy `python main_pipeline.py` trước để tạo dữ liệu.")
        return

    # ── Bộ lọc ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**🔧 Chọn thông số dự báo**")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    category = c1.selectbox("Danh mục", list(CAT_VI.keys()),
                             format_func=lambda x: CAT_VI[x])
    year     = c2.selectbox("Năm", [2014, 2015, 2016, 2017], index=3)
    month    = c3.selectbox("Tháng", list(range(1, 13)), index=10,
                             format_func=lambda m: MONTH_VI[m])
    run_btn  = c4.button("▶ Chạy Dự báo", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Biểu đồ lịch sử ─────────────────────────────────────────────────────
    cat_df = monthly[monthly["Category"] == category].sort_values("YearMonth")
    target = (cat_df["Year"] == year) & (cat_df["Month"] == month)

    st.markdown('<div class="card" style="padding-bottom:4px;">', unsafe_allow_html=True)
    st.markdown(f"**📅 Lịch sử doanh thu — {CAT_VI[category]}**")

    color = CAT_COLOR.get(category, "#2563EB")
    fill  = CAT_FILL.get(category, "rgba(37,99,235,0.08)")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cat_df["YearMonth"], y=cat_df["TotalSales"],
        name="Lịch sử", mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=fill,
    ))
    if target.any():
        t = cat_df[target]
        fig.add_trace(go.Scatter(
            x=t["YearMonth"], y=t["TotalSales"],
            name="Kỳ chọn", mode="markers",
            marker=dict(color="#DC2626", size=12, symbol="diamond",
                        line=dict(color="#FFFFFF", width=2)),
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Be Vietnam Pro", color="#64748B", size=13),
        xaxis=dict(showgrid=False, zeroline=False, tickformat="%m/%Y", tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, tickprefix="$"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#0F172A")),
        margin=dict(l=0, r=0, t=8, b=0), height=220,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Kết quả dự báo ──────────────────────────────────────────────────────
    if run_btn or "last_forecast" in st.session_state:
        if run_btn:
            with st.spinner("Đang chạy TS-RAG pipeline…"):
                analysis = run_forecast(category, year, month)
            st.session_state["last_forecast"] = analysis
        else:
            analysis = st.session_state.get("last_forecast")

        if not analysis:
            st.error("Không thể tạo dự báo.")
            return

        conf  = analysis["confidence"]
        color = "#16A34A" if conf >= 0.8 else "#DC2626" if conf < 0.7 else "#D97706"
        bg    = "#F0FDF4" if conf >= 0.8 else "#FEF2F2" if conf < 0.7 else "#FFFBEB"

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Kết quả chính
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {color};background:{bg};">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                        flex-wrap:wrap;gap:16px;">
                <div>
                    <div style="font-size:13px;font-weight:700;color:#64748B;
                                text-transform:uppercase;letter-spacing:.05em;">
                        Dự báo doanh thu · {analysis["period"]}
                    </div>
                    <div style="font-size:2.5rem;font-weight:800;color:{color};
                                line-height:1.1;margin-top:6px;">
                        ${analysis["forecast_sales"]:,}
                    </div>
                    <div style="font-size:14px;color:#64748B;margin-top:4px;">
                        Khoảng: ${analysis["forecast_range"]["low"]:,} – ${analysis["forecast_range"]["high"]:,}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:13px;font-weight:600;color:#64748B;">Độ tin cậy</div>
                    <div style="font-size:2rem;font-weight:800;color:{color};">{conf:.0%}</div>
                    <div style="font-size:13px;color:#64748B;margin-top:4px;">
                        {analysis["reasoning_type"].replace("_"," ")}
                    </div>
                </div>
            </div>
            <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(0,0,0,.08);
                        font-size:15px;font-weight:600;color:#0F172A;">
                💡 {analysis["recommendation"]}
                <span style="font-weight:400;color:#64748B;"> · Điều chỉnh tồn kho: {analysis["stock_adjustment"]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Drivers & Risks
        col_d, col_r = st.columns(2)
        with col_d:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**✅ Yếu tố thúc đẩy**")
            if analysis["key_drivers"]:
                for d in analysis["key_drivers"]:
                    st.markdown(f"""
                    <div style="display:flex;gap:10px;align-items:flex-start;
                                padding:10px 0;border-bottom:1px solid #F1F5F9;">
                        <span style="color:#16A34A;font-size:16px;flex-shrink:0;">✓</span>
                        <span style="font-size:14px;color:#0F172A;line-height:1.5;">{d}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#64748B;font-size:14px;">Không có yếu tố nổi bật.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**⚠️ Rủi ro cần lưu ý**")
            if analysis["risks"]:
                for r in analysis["risks"]:
                    st.markdown(f"""
                    <div style="display:flex;gap:10px;align-items:flex-start;
                                padding:10px 0;border-bottom:1px solid #F1F5F9;">
                        <span style="color:#D97706;font-size:16px;flex-shrink:0;">⚠</span>
                        <span style="font-size:14px;color:#0F172A;line-height:1.5;">{r}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#16A34A;font-size:14px;">✓ Không phát hiện rủi ro đáng kể.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bảng mẫu tương tự
        patterns = analysis.get("retrieved_patterns", [])
        if patterns:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**🔍 Mẫu lịch sử tương tự được truy xuất**")
            rows = [{"Kỳ": p["yearmonth"], "Doanh thu TB": f"${p['avg_sales']:,.0f}",
                     "Đỉnh": f"${p['peak_sales']:,.0f}",
                     "Xu hướng 6 tháng": f"{p['sales_trend_pct']:+.1f}%",
                     "Độ tương đồng": f"{p['similarity']:.1%}"} for p in patterns]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("🔍 Xem ngữ cảnh RAG đầy đủ"):
            st.code(analysis.get("context", ""), language="markdown")