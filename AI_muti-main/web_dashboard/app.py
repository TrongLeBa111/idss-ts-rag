"""
web_dashboard/app.py
IDSS Dashboard — Navbar trên + Sidebar trái hướng dẫn
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import streamlit as st

st.set_page_config(
    page_title="IDSS — Hỗ trợ Ra Quyết định",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

/* ── Reset toàn bộ ── */
* { font-family: 'Be Vietnam Pro', sans-serif !important; box-sizing: border-box; }
.stApp { background: #F8FAFC !important; }
.block-container {
    padding: 0 0 0 0 !important;
    max-width: 100% !important;
}
.main > div { padding: 0 !important; }

/* ── Ẩn chrome mặc định Streamlit ── */
#MainMenu, footer,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {
    display: none !important;
}

/* ── Ẩn header mặc định nhưng giữ sidebar toggle ── */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* ── CSS variables ── */
:root {
    --primary:      #2563EB;
    --primary-dark: #1D4ED8;
    --primary-light:#EFF6FF;
    --success:      #16A34A;
    --success-bg:   #F0FDF4;
    --warning:      #D97706;
    --warning-bg:   #FFFBEB;
    --danger:       #DC2626;
    --danger-bg:    #FEF2F2;
    --bg:           #F8FAFC;
    --white:        #FFFFFF;
    --border:       #E2E8F0;
    --text:         #0F172A;
    --muted:        #64748B;
    --light:        #94A3B8;
    --radius:       10px;
    --shadow:       0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md:    0 4px 12px rgba(0,0,0,.08);
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    min-width: 230px !important;
    max-width: 270px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}
[data-testid="stSidebarUserContent"] {
    padding: 0 !important;
}

/* ── Navbar cố định trên cùng ── */
.idss-navbar {
    position: sticky; top: 0; z-index: 9999;
    background: var(--white);
    border-bottom: 1px solid var(--border);
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 0 32px;
    display: flex; align-items: center; justify-content: space-between;
    height: 60px;
}
.navbar-brand {
    display: flex; align-items: center; gap: 10px;
}
.navbar-logo {
    background: var(--primary); border-radius: 8px;
    width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.navbar-title  { font-size: 17px; font-weight: 800; color: var(--text); line-height: 1.2; }
.navbar-sub    { font-size: 11px; color: var(--muted); font-weight: 500; }
.navbar-links  { display: flex; align-items: center; gap: 4px; }
.nav-tab {
    padding: 8px 16px; border-radius: 8px;
    font-size: 14px; font-weight: 600; color: var(--muted);
    cursor: pointer; border: none; background: transparent;
    transition: all .15s; white-space: nowrap; text-decoration: none;
    display: inline-flex; align-items: center; gap: 6px;
}
.nav-tab:hover  { background: var(--primary-light); color: var(--primary); }
.nav-tab.active { background: var(--primary-light); color: var(--primary); }
.navbar-badge {
    display: flex; align-items: center; gap: 5px;
    background: var(--success-bg); border: 1px solid #BBF7D0;
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 700; color: var(--success);
}
.badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--success); display: inline-block;
}

/* ── Nội dung chính ── */
.idss-main { padding: 24px 28px; }

/* ── Cards ── */
.card {
    background: var(--white); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px 24px;
    box-shadow: var(--shadow);
}
.page-header {
    background: var(--white); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px 24px;
    box-shadow: var(--shadow); margin-bottom: 20px;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--white) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; padding: 18px 20px !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="metric-container"] label {
    font-size: 12px !important; font-weight: 700 !important;
    color: var(--muted) !important; text-transform: uppercase; letter-spacing: .06em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.9rem !important; font-weight: 800 !important; color: var(--primary) !important;
}

/* ── Form elements ── */
[data-baseweb="select"] > div {
    background: var(--white) !important; border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important; font-size: 15px !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.1) !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: var(--primary) !important; color: #fff !important;
    border: none !important; border-radius: var(--radius) !important;
    font-size: 15px !important; font-weight: 700 !important;
    padding: 10px 24px !important; box-shadow: var(--shadow-md) !important;
    transition: all .2s !important;
}
.stButton > button[kind="primary"]:hover { background: var(--primary-dark) !important; }
.stButton > button:not([kind="primary"]) {
    background: var(--white) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important; border-radius: var(--radius) !important;
    font-size: 15px !important; font-weight: 600 !important; padding: 10px 20px !important;
}
.stButton > button:not([kind="primary"]):hover { background: var(--primary-light) !important; }
.stDownloadButton > button {
    background: var(--white) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important; border-radius: var(--radius) !important;
    font-weight: 600 !important; font-size: 15px !important;
}

/* ── Radio ── */
[data-testid="stRadio"] > div { gap: 2px !important; }
[data-testid="stRadio"] > div > label {
    padding: 8px 14px !important; border-radius: 8px !important;
    font-size: 14px !important; font-weight: 500 !important; color: var(--muted) !important;
}
[data-testid="stRadio"] > div > label:hover { background: var(--primary-light) !important; color: var(--primary) !important; }
[data-testid="stRadio"] > div > label[data-checked="true"] {
    background: var(--primary-light) !important; color: var(--primary) !important; font-weight: 700 !important;
}
[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }

/* ── Sidebar nav buttons ── */
.sidebar-nav-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #64748B;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all .15s;
    text-align: left;
    margin-bottom: 2px;
}
.sidebar-nav-btn:hover {
    background: #EFF6FF;
    color: #2563EB;
}
.sidebar-nav-btn.active {
    background: #EFF6FF;
    color: #2563EB;
    font-weight: 700;
}
.sidebar-section-title {
    font-size: 10px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: .08em;
    padding: 16px 16px 6px;
}
.sidebar-divider {
    height: 1px;
    background: #E2E8F0;
    margin: 8px 12px;
}
.sidebar-info-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 8px 12px;
    font-size: 12.5px;
    color: #1D4ED8;
    line-height: 1.6;
}
.sidebar-tip {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 12px;
    font-size: 12px;
    color: #16A34A;
    line-height: 1.5;
}
.sidebar-warn {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 12px;
    font-size: 12px;
    color: #D97706;
    line-height: 1.5;
}

/* ── Misc ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stExpander"]  { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; background: var(--white) !important; }
h1 { font-size: 1.6rem !important; font-weight: 800 !important; color: var(--text) !important; letter-spacing: -.02em; margin: 0 0 4px !important; }
h2 { font-size: 1.15rem !important; font-weight: 700 !important; color: var(--text) !important; margin: 0 0 12px !important; }
p  { font-size: 15px; line-height: 1.6; color: var(--muted); margin: 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Page definitions ────────────────────────────────────────────────────────
PAGES = {
    "home":     ("🏠", "Tổng quan"),
    "forecast": ("📈", "Phân tích Dự báo"),
    "anomaly":  ("🚨", "Phát hiện Bất thường"),
    "audit":    ("📋", "Nhật ký Kiểm toán"),
}

if "page" not in st.session_state:
    st.session_state.page = "home"


# ── LEFT SIDEBAR ────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div style="padding:20px 16px 12px;border-bottom:1px solid #E2E8F0;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="background:#2563EB;border-radius:8px;width:34px;height:34px;
                        display:flex;align-items:center;justify-content:center;font-size:16px;">📊</div>
            <div>
                <div style="font-size:15px;font-weight:800;color:#0F172A;line-height:1.2;">IDSS</div>
                <div style="font-size:10px;color:#64748B;font-weight:500;">Hỗ trợ Ra Quyết định</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown('<div class="sidebar-section-title">📌 Điều hướng</div>', unsafe_allow_html=True)

    for code, (icon, label) in PAGES.items():
        is_active = st.session_state.page == code
        btn_style = (
            "background:#EFF6FF;color:#2563EB;font-weight:700;" if is_active
            else "background:transparent;color:#64748B;font-weight:600;"
        )
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{code}",
            use_container_width=True,
            help=f"Chuyển sang trang {label}",
        ):
            st.session_state.page = code
            st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # Page-specific guidance
    page = st.session_state.page

    if page == "home":
        st.markdown('<div class="sidebar-section-title">📊 Tổng quan</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="sidebar-info-box">
            📅 <strong>Bộ lọc năm &amp; danh mục</strong> nằm ngay trên đầu trang — chọn để lọc dữ liệu tương ứng.
        </div>
        <div class="sidebar-tip">
            ✅ Dữ liệu 2014–2017, chia theo 3 danh mục: Nội thất, Công nghệ, Văn phòng phẩm.
        </div>
        <div class="sidebar-section-title" style="margin-top:8px;">📌 Trong trang này</div>
        <div style="padding:0 16px;font-size:13px;color:#64748B;line-height:2;">
            • KPIs tổng hợp<br>
            • Doanh thu theo thời gian<br>
            • Tỷ lệ danh mục (donut)<br>
            • Dự báo AI mới nhất
        </div>
        """, unsafe_allow_html=True)

    elif page == "forecast":
        st.markdown('<div class="sidebar-section-title">📈 Dự báo</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="sidebar-info-box">
            🔧 <strong>Chọn danh mục, năm, tháng</strong> rồi nhấn <em>▶ Chạy Dự báo</em> để kích hoạt TS-RAG.
        </div>
        <div class="sidebar-tip">
            ✅ TS-RAG truy xuất mẫu lịch sử tương đồng và suy luận ngữ cảnh theo thời gian thực.
        </div>
        <div class="sidebar-warn">
            ⚠ Cần chạy <code>main_pipeline.py</code> trước để có dữ liệu vector.
        </div>
        <div class="sidebar-section-title" style="margin-top:8px;">📌 Trong trang này</div>
        <div style="padding:0 16px;font-size:13px;color:#64748B;line-height:2;">
            • Biểu đồ lịch sử doanh thu<br>
            • Kết quả dự báo + khoảng tin cậy<br>
            • Yếu tố thúc đẩy &amp; rủi ro<br>
            • Mẫu lịch sử tương tự (RAG)
        </div>
        """, unsafe_allow_html=True)

    elif page == "anomaly":
        st.markdown('<div class="sidebar-section-title">🚨 Bất thường</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="sidebar-info-box">
            ⚙️ <strong>Chọn danh mục</strong> và <strong>mức nhạy (Z-score)</strong> để điều chỉnh độ nhạy phát hiện.
        </div>
        <div class="sidebar-tip">
            ✅ Z ≥ 1.8: Tiêu chuẩn — phát hiện nhiều điểm hơn.<br>
            ✅ Z ≥ 2.5: Chặt chẽ — chỉ tháng thực sự bất thường.
        </div>
        <div class="sidebar-section-title" style="margin-top:8px;">📌 Trong trang này</div>
        <div style="padding:0 16px;font-size:13px;color:#64748B;line-height:2;">
            • KPI: Tổng / Nghiêm trọng / Tăng / Giảm<br>
            • Biểu đồ Z-score band<br>
            • Danh sách chi tiết bất thường<br>
            • Thanh progress Z-score
        </div>
        """, unsafe_allow_html=True)

    elif page == "audit":
        st.markdown('<div class="sidebar-section-title">📋 Kiểm toán</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="sidebar-info-box">
            🔍 <strong>Lọc theo loại hành động</strong> và <strong>mức tin cậy</strong> để xem các quyết định AI tương ứng.
        </div>
        <div class="sidebar-tip">
            ✅ Tuân thủ Luật AI 2025 — mọi quyết định đều được ghi nhận và có thể xuất CSV.
        </div>
        <div class="sidebar-section-title" style="margin-top:8px;">📌 Trong trang này</div>
        <div style="padding:0 16px;font-size:13px;color:#64748B;line-height:2;">
            • KPI: Tổng / Độ tin cậy TB<br>
            • Bộ lọc hành động &amp; tin cậy<br>
            • Timeline nhật ký màu sắc<br>
            • Xuất CSV UTF-8
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="sidebar-divider"></div>
    <div style="padding:8px 16px 16px;font-size:11px;color:#94A3B8;line-height:1.6;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span style="width:6px;height:6px;border-radius:50%;background:#16A34A;display:inline-block;"></span>
            <strong style="color:#16A34A;">Hệ thống hoạt động</strong>
        </div>
        IDSS v1.0 · TS-RAG Engine<br>
        Dữ liệu: Superstore 2014–2017
    </div>
    """, unsafe_allow_html=True)


# ── TOP NAVBAR ──────────────────────────────────────────────────────────────
current_page = st.session_state.page

tabs_html = "".join(
    f'<span class="nav-tab{" active" if current_page == code else ""}">'
    f'{icon}&nbsp;{label}</span>'
    for code, (icon, label) in PAGES.items()
)

st.markdown(f"""
<div class="idss-navbar">
    <div class="navbar-brand">
        <div class="navbar-logo">📊</div>
        <div>
            <div class="navbar-title">IDSS</div>
            <div class="navbar-sub">Hỗ trợ Ra Quyết định thông minh</div>
        </div>
    </div>
    <div class="navbar-links">{tabs_html}</div>
    <div class="navbar-badge">
        <span class="badge-dot"></span> Hệ thống hoạt động
    </div>
</div>
<div class="idss-main">
""", unsafe_allow_html=True)


# ── ROUTE ──────────────────────────────────────────────────────────────────
if current_page == "home":
    from web_dashboard.pages.home import render
elif current_page == "forecast":
    from web_dashboard.pages.forecast_analysis import render
elif current_page == "anomaly":
    from web_dashboard.pages.anomaly_detection import render
else:
    from web_dashboard.pages.audit_logs import render

render()
st.markdown("</div>", unsafe_allow_html=True)