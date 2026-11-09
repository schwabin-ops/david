import streamlit as st
import requests
import time

# ==========================================
# DAVID FINANCE - STREAMLIT
# ==========================================

URL = "https://david-ai-arjg.onrender.com/finance"
HOME_URL = "https://david-ai-arjg.onrender.com"

st.set_page_config(
    page_title="DAVID Finance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>
    header {visibility: hidden;}

    #MainMenu {visibility: hidden;}

    footer {visibility: hidden;}

    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .stApp {
        background: #080b12;
    }

    iframe {
        border: none !important;
    }

    .topbar {
        background: #101722;
        padding: 15px 24px;
        border-bottom: 1px solid #263244;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .brand {
        color: white;
        font-size: 22px;
        font-weight: 800;
    }

    .status {
        color: #35d49a;
        font-size: 12px;
    }

    .info {
        color: #9ba9bb;
        font-size: 13px;
    }

    .main-title {
        color: white;
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="topbar">
    <div class="brand">DAVID FINANCE</div>
    <div class="status">● FINANCE PLATFORM</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# SERVER CONNECTION CHECK
# ==========================================

@st.cache_data(ttl=30)
def check_server():
    try:
        response = requests.get(
            URL,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        return {
            "connected": response.status_code < 500,
            "status": response.status_code,
            "message": "서버 응답 확인"
        }

    except requests.exceptions.Timeout:
        return {
            "connected": False,
            "status": None,
            "message": "서버 응답 시간 초과"
        }

    except requests.exceptions.RequestException as e:
        return {
            "connected": False,
            "status": None,
            "message": str(e)
        }

# ==========================================
# MAIN
# ==========================================

st.markdown("""
<div style="padding:20px 24px 5px 24px">
    <div class="main-title">Financial Intelligence Dashboard</div>
    <div class="info">
        DAVID AI Financial Platform
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# CONNECTION STATUS
# ==========================================

with st.spinner("DAVID Finance 서버 연결 확인 중..."):
    server = check_server()

if server["connected"]:

    st.success(
        f"원본 서버 응답 확인 · HTTP {server['status']}"
    )

    st.markdown(
        '<div style="height:8px"></div>',
        unsafe_allow_html=True
    )

    # ======================================
    # ORIGINAL WEBSITE
    # ======================================

    st.iframe(
        URL,
        height=1000,
        width="stretch"
    )

else:

    st.error("원본 서버에 연결할 수 없습니다.")

    st.warning(
        f"상세 정보: {server['message']}"
    )

    st.markdown("### 원본 페이지 접속")

    st.link_button(
        "DAVID Finance 직접 열기",
        URL,
        use_container_width=True
    )

    st.link_button(
        "DAVID 홈페이지 열기",
        HOME_URL,
        use_container_width=True
    )

    if st.button("서버 다시 확인", use_container_width=True):
        check_server.clear()
        st.rerun()

# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div style="
    padding:20px;
    text-align:center;
    color:#718096;
    font-size:11px;
    border-top:1px solid #263244;
    margin-top:20px;
">
    DAVID FINANCE · POWERED BY DAVID AI
</div>
""", unsafe_allow_html=True)
