import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# YOUNGKK | Global Financial Intelligence
# Streamlit single-file application
# ============================================================

st.set_page_config(
    page_title="영크크 | Global Financial Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------- STYLE ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
:root {
    --bg: #080b0f;
    --panel: #10161d;
    --panel2: #141d26;
    --line: #273442;
    --muted: #8292a3;
    --text: #e5edf5;
    --orange: #f39a35;
    --green: #35c98a;
    --red: #ff626b;
    --blue: #68a9e8;
}
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
.block-container { max-width: 1600px; padding-top: 1rem; padding-bottom: 2rem; }
header, footer, #MainMenu { visibility: hidden; }
[data-testid="stSidebar"] { background: #0d131a; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: var(--text); }
h1, h2, h3 { color: var(--text) !important; letter-spacing: -.02em; }
p, label, span { color: inherit; }
.terminal-top {
    display:flex; justify-content:space-between; align-items:center;
    border-bottom: 2px solid var(--orange); padding: 4px 0 12px 0; margin-bottom: 14px;
}
.brand { font-family:'IBM Plex Mono', monospace; font-weight:700; font-size:25px; letter-spacing:2px; color:#fff; }
.brand span { color:var(--orange); }
.top-meta { color:var(--muted); font-family:'IBM Plex Mono', monospace; font-size:11px; text-align:right; }
.section-kicker {
    color:var(--orange); font-family:'IBM Plex Mono', monospace; font-size:11px;
    font-weight:700; letter-spacing:1.4px; text-transform:uppercase; margin: 8px 0;
}
.panel {
    background:var(--panel); border:1px solid var(--line); border-radius:4px;
    padding:12px 14px; min-height:88px;
}
.metric-label { color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:1px; }
.metric-value { color:#f3f6fa; font-family:'IBM Plex Mono',monospace; font-size:22px; font-weight:600; margin-top:7px; }
.metric-change { font-family:'IBM Plex Mono',monospace; font-size:12px; margin-top:4px; }
.up { color:var(--green); } .down { color:var(--red); } .neutral { color:var(--muted); }
.news-item { border-bottom:1px solid var(--line); padding:10px 0 12px 0; }
.news-title { color:#e7edf4; font-weight:600; font-size:14px; line-height:1.45; }
.news-meta { color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:10px; margin-top:5px; }
.small-note { color:var(--muted); font-size:11px; }
div[data-testid="stMetric"] {
    background:var(--panel); border:1px solid var(--line); border-radius:4px;
    padding:12px 14px;
}
div[data-testid="stMetricLabel"] { color:var(--muted); }
div[data-testid="stMetricValue"] { font-family:'IBM Plex Mono',monospace; color:#fff; }
.stButton>button, .stDownloadButton>button {
    border-radius:3px; border:1px solid var(--line); background:#18232e; color:#e9f0f7;
}
.stButton>button:hover { border-color:var(--orange); color:#fff; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
.stDateInput input, .stNumberInput input {
    background:#111923; color:#e5edf5; border-color:var(--line);
}
hr { border-color:var(--line); }
a { color:#8dbdf0 !important; text-decoration:none; }
a:hover { color:var(--orange) !important; }
[data-testid="stDataFrame"] { border:1px solid var(--line); }
</style>
""", unsafe_allow_html=True)

# --------------------------- STATE ---------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "MSFT", "NVDA", "005930.KS", "TSLA"]
if "groups" not in st.session_state:
    st.session_state.groups = {"CORE": ["AAPL", "MSFT", "NVDA"], "KOREA": ["005930.KS", "000660.KS"]}
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "community_posts" not in st.session_state:
    st.session_state.community_posts = []

# --------------------------- HELPERS ---------------------------
INDEXES = {
    "S&P 500": "^GSPC", "NASDAQ Composite": "^IXIC", "Dow Jones": "^DJI",
    "KOSPI": "^KS11", "KOSDAQ": "^KQ11", "Nikkei 225": "^N225",
    "Hang Seng": "^HSI", "FTSE 100": "^FTSE", "DAX": "^GDAXI",
    "VIX": "^VIX", "US Dollar Index": "DX-Y.NYB",
    "Gold": "GC=F", "WTI Crude": "CL=F", "Bitcoin": "BTC-USD",
    "USD/KRW": "KRW=X"
}
POPULAR = {
    "Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA",
    "Alphabet": "GOOGL", "Amazon": "AMZN", "Meta": "META",
    "Tesla": "TSLA", "Samsung Electronics": "005930.KS",
    "SK hynix": "000660.KS", "Hyundai Motor": "005380.KS",
    "Kakao": "035720.KS", "LG Energy Solution": "373220.KS",
    "Berkshire Hathaway": "BRK-B", "JPMorgan": "JPM"
}
PERIODS = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "MAX": "max"}

def safe_num(value, digits=2):
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "N/A"

def safe_pct(value):
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):+.2f}%"
    except Exception:
        return "N/A"

def fetch_history(symbol, period="1y", interval=None):
    try:
        ticker = yf.Ticker(symbol)
        kwargs = {"period": period, "auto_adjust": True}
        if interval:
            kwargs["interval"] = interval
        df = ticker.history(**kwargs)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

def fetch_quote(symbol):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d", auto_adjust=False)
        info = {}
        if hist is None or hist.empty:
            return {"symbol": symbol, "price": None, "change": None, "pct": None, "info": info}
        close = hist["Close"].dropna()
        price = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else price
        change = price - previous
        pct = (change / previous * 100) if previous else 0
        return {"symbol": symbol, "price": price, "change": change, "pct": pct, "info": info}
    except Exception:
        return {"symbol": symbol, "price": None, "change": None, "pct": None, "info": {}}

@st.cache_data(ttl=180, show_spinner=False)
def cached_quote(symbol):
    return fetch_quote(symbol)

@st.cache_data(ttl=300, show_spinner=False)
def cached_history(symbol, period):
    return fetch_history(symbol, period)

@st.cache_data(ttl=300, show_spinner=False)
def google_news(query, language="en", country="US", limit=20):
    hl_gl = {
        ("ko", "KR"): ("ko", "KR", "KR:ko"),
        ("en", "US"): ("en-US", "US", "US:en"),
        ("en", "GB"): ("en-GB", "GB", "GB:en"),
    }
    hl, gl, ceid = hl_gl.get((language, country), ("en-US", "US", "US:en"))
    q = quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
    try:
        feed = feedparser.parse(url)
        rows = []
        for item in feed.entries[:limit]:
            rows.append({
                "title": item.get("title", "Untitled"),
                "link": item.get("link", ""),
                "published": item.get("published", ""),
                "source": item.get("source", {}).get("title", "Google News"),
                "summary": item.get("summary", "")
            })
        return rows
    except Exception:
        return []

@st.cache_data(ttl=300, show_spinner=False)
def yahoo_news(symbol):
    try:
        items = yf.Ticker(symbol).news or []
        out = []
        for item in items[:15]:
            content = item.get("content", item)
            title = content.get("title", "")
            canonical = content.get("canonicalUrl") or {}
            click = canonical.get("url", "") if isinstance(canonical, dict) else ""
            provider = content.get("provider") or {}
            out.append({
                "title": title,
                "link": click,
                "published": content.get("pubDate", ""),
                "source": provider.get("displayName", "Yahoo Finance"),
                "summary": content.get("summary", "")
            })
        return out
    except Exception:
        return []

def render_news(items, max_items=15):
    if not items:
        st.info("현재 불러올 수 있는 뉴스가 없습니다. 잠시 후 다시 시도해 주세요.")
        return
    for item in items[:max_items]:
        title = item.get("title", "Untitled")
        link = item.get("link", "")
        source = item.get("source", "")
        published = item.get("published", "")
        summary = item.get("summary", "")
        st.markdown(
            f"""<div class="news-item">
            <div class="news-title"><a href="{link}" target="_blank">{title}</a></div>
            <div class="news-meta">{source} &nbsp; | &nbsp; {published}</div>
            </div>""",
            unsafe_allow_html=True
        )
        if summary:
            with st.expander("요약 정보"):
                st.write(pd.Series([summary]).iloc[0][:700])

def market_card(label, symbol):
    q = cached_quote(symbol)
    price, pct = q["price"], q["pct"]
    if price is None:
        st.metric(label, "N/A", "데이터 없음")
    else:
        st.metric(label, safe_num(price), safe_pct(pct),
                  delta_color="normal")

def make_chart(df, symbol, title):
    if df.empty:
        st.warning("가격 데이터를 불러오지 못했습니다.")
        return
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name=symbol
    ))
    fig.update_layout(
        title=title, template="plotly_dark", height=470,
        paper_bgcolor="#10161d", plot_bgcolor="#10161d",
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_rangeslider_visible=False,
        font=dict(family="IBM Plex Mono", color="#dce5ee"),
    )
    st.plotly_chart(fig, use_container_width=True)

def company_info(symbol):
    try:
        return yf.Ticker(symbol).get_info()
    except Exception:
        return {}

def show_table(data, empty_message="표시할 데이터가 없습니다."):
    if data is None:
        st.info(empty_message)
    elif isinstance(data, pd.DataFrame):
        if data.empty:
            st.info(empty_message)
        else:
            st.dataframe(data, use_container_width=True)
    else:
        st.write(data)

# --------------------------- HEADER ---------------------------
now = datetime.now().astimezone()
st.markdown(f"""
<div class="terminal-top">
  <div>
    <div class="brand">영크크</div>
    <div style="font-family:IBM Plex Mono;color:#8292a3;font-size:10px;letter-spacing:2px">
      GLOBAL FINANCIAL INTELLIGENCE
    </div>
  </div>
  <div class="top-meta">
    MARKET INFORMATION SYSTEM<br>
    {now.strftime("%Y-%m-%d %H:%M:%S %Z")}
  </div>
</div>
""", unsafe_allow_html=True)

# --------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.markdown("## 영크크")
    st.caption("GLOBAL MARKETS / RESEARCH")
    page = st.radio(
        "WORKSPACE",
        ["시장 종합", "뉴스 센터", "종목 분석", "관심종목", "시장 스크리너",
         "기업 재무", "투자 캘린더", "옵션 데이터", "내부자 거래", "공시 자료", "커뮤니티", "설정"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("#### 빠른 종목 검색")
    quick_symbol = st.text_input("티커 입력", value="", placeholder="예: AAPL, 005930.KS")
    if quick_symbol.strip() and st.button("종목 열기", use_container_width=True):
        st.session_state.selected_symbol = quick_symbol.strip().upper()
        st.session_state.open_stock_page = True
        st.rerun()
    st.divider()
    st.markdown("#### 데이터 안내")
    st.caption("가격·재무 데이터: Yahoo Finance 연동")
    st.caption("뉴스: Google News RSS 및 Yahoo Finance")
    st.caption("일부 거래소 데이터는 지연되거나 제공되지 않을 수 있습니다.")

# --------------------------- GLOBAL MARKET STRIP ---------------------------
st.markdown('<div class="section-kicker">GLOBAL MARKET SNAPSHOT</div>', unsafe_allow_html=True)
strip_names = ["S&P 500", "NASDAQ Composite", "Dow Jones", "KOSPI", "KOSDAQ", "Nikkei 225"]
cols = st.columns(6)
for col, name in zip(cols, strip_names):
    with col:
        market_card(name, INDEXES[name])

st.divider()

# --------------------------- PAGE: MARKET OVERVIEW ---------------------------
if page == "시장 종합":
    st.markdown("## 시장 종합")
    st.caption("글로벌 주요 지수, 원자재, 환율 및 가상자산의 시장 현황")
    names = list(INDEXES.items())
    rows = []
    progress = st.progress(0)
    for i, (name, symbol) in enumerate(names):
        q = cached_quote(symbol)
        rows.append({
            "자산": name, "티커": symbol,
            "현재가": q["price"], "등락": q["change"], "등락률(%)": q["pct"]
        })
        progress.progress((i + 1) / len(names))
    progress.empty()
    df = pd.DataFrame(rows)
    if not df.empty:
        st.dataframe(
            df.style.format({"현재가": "{:,.2f}", "등락": "{:+,.2f}", "등락률(%)": "{:+.2f}%"}),
            use_container_width=True, hide_index=True
        )
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("### 주요 시장 뉴스")
        news = google_news("global stock market OR economy OR central bank", "en", "US", 12)
        render_news(news, 12)
    with right:
        st.markdown("### 한국 금융 뉴스")
        news_kr = google_news("증시 OR 금융시장 OR 한국은행 OR 환율", "ko", "KR", 12)
        render_news(news_kr, 12)

# --------------------------- PAGE: NEWS ---------------------------
elif page == "뉴스 센터":
    st.markdown("## 뉴스 센터")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        query = st.text_input("뉴스 검색", value="global financial markets")
    with c2:
        lang = st.selectbox("언어", ["한국어", "English"])
    with c3:
        country = st.selectbox("지역", ["한국", "미국", "영국"])
    language = "ko" if lang == "한국어" else "en"
    country_code = {"한국": "KR", "미국": "US", "영국": "GB"}[country]
    tab1, tab2 = st.tabs(["Google News", "Yahoo Finance"])
    with tab1:
        render_news(google_news(query, language, country_code, 40), 40)
    with tab2:
        symbol_for_news = st.text_input("Yahoo Finance 종목 티커", "AAPL")
        render_news(yahoo_news(symbol_for_news.upper()), 20)

# --------------------------- PAGE: STOCK ANALYSIS ---------------------------
elif page == "종목 분석":
    st.markdown("## 종목 분석")
    default_symbol = st.session_state.get("selected_symbol", "AAPL")
    symbol = st.text_input("종목 티커", default_symbol).strip().upper()
    period_label = st.radio("차트 기간", list(PERIODS.keys()), horizontal=True, index=4)
    if symbol:
        q = cached_quote(symbol)
        info = company_info(symbol)
        company = info.get("longName") or info.get("shortName") or symbol
        st.markdown(f"### {company}  ·  `{symbol}`")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("현재가", safe_num(q["price"]), safe_pct(q["pct"]))
        m2.metric("시가총액", f"{info.get('marketCap', 0):,.0f}" if info.get("marketCap") else "N/A")
        m3.metric("PER", safe_num(info.get("trailingPE")))
        m4.metric("EPS", safe_num(info.get("trailingEps")))
        m5.metric("배당수익률", safe_pct((info.get("dividendYield") or 0) * 100))
        history = cached_history(symbol, PERIODS[period_label])
        make_chart(history, symbol, f"{company} / Price History")
        tabs = st.tabs(["개요", "뉴스", "애널리스트", "재무 요약", "배당·이벤트"])
        with tabs[0]:
            a, b = st.columns(2)
            with a:
                st.markdown("#### 기업 개요")
                st.write(info.get("longBusinessSummary", "기업 설명을 제공하지 않습니다."))
            with b:
                st.markdown("#### 주요 지표")
                fields = {
                    "업종": info.get("industry"), "섹터": info.get("sector"),
                    "직원 수": info.get("fullTimeEmployees"), "국가": info.get("country"),
                    "웹사이트": info.get("website"), "52주 최고": info.get("fiftyTwoWeekHigh"),
                    "52주 최저": info.get("fiftyTwoWeekLow"), "평균 거래량": info.get("averageVolume")
                }
                st.dataframe(pd.DataFrame(fields.items(), columns=["항목", "값"]), hide_index=True, use_container_width=True)
        with tabs[1]:
            render_news(yahoo_news(symbol), 20)
            st.markdown("#### Google News")
            render_news(google_news(f"{symbol} stock company", "en", "US", 15), 15)
        with tabs[2]:
            analyst = {
                "목표주가 평균": info.get("targetMeanPrice"),
                "목표주가 최고": info.get("targetHighPrice"),
                "목표주가 최저": info.get("targetLowPrice"),
                "분석가 수": info.get("numberOfAnalystOpinions"),
                "추천 의견": info.get("recommendationKey")
            }
            st.dataframe(pd.DataFrame(analyst.items(), columns=["지표", "값"]), hide_index=True, use_container_width=True)
            st.caption("애널리스트 데이터는 제공 종목과 시점에 따라 누락될 수 있습니다. 투자 판단의 근거로 단독 사용하지 마세요.")
        with tabs[3]:
            try:
                t = yf.Ticker(symbol)
                st.markdown("#### 손익계산서")
                show_table(t.financials)
                st.markdown("#### 대차대조표")
                show_table(t.balance_sheet)
                st.markdown("#### 현금흐름표")
                show_table(t.cashflow)
            except Exception as e:
                st.warning(f"재무제표를 불러오지 못했습니다: {e}")
        with tabs[4]:
            try:
                t = yf.Ticker(symbol)
                st.markdown("#### 배당 내역")
                show_table(t.dividends.tail(20).to_frame("배당금"))
                st.markdown("#### 기업 일정")
                show_table(t.calendar)
            except Exception:
                st.info("배당 또는 일정 데이터가 제공되지 않습니다.")
        if st.button("관심종목에 추가", key="add_stock"):
            if symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(symbol)
                st.success(f"{symbol}을(를) 관심종목에 추가했습니다.")

# --------------------------- PAGE: WATCHLIST ---------------------------
elif page == "관심종목":
    st.markdown("## 관심종목")
    st.caption("현재 브라우저 세션에 저장되는 관심종목 목록입니다.")
    new_symbol = st.text_input("티커 추가", placeholder="예: NVDA")
    if st.button("추가", key="watch_add") and new_symbol.strip():
        sym = new_symbol.strip().upper()
        if sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(sym)
    if st.session_state.watchlist:
        rows = []
        for sym in st.session_state.watchlist:
            q = cached_quote(sym)
            rows.append({"티커": sym, "현재가": q["price"], "등락": q["change"], "등락률(%)": q["pct"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        remove_symbol = st.selectbox("삭제할 종목", ["선택 안 함"] + st.session_state.watchlist)
        if st.button("선택 종목 삭제") and remove_symbol != "선택 안 함":
            st.session_state.watchlist.remove(remove_symbol)
            st.rerun()
    else:
        st.info("관심종목이 없습니다.")
    st.markdown("### 관심종목 그룹")
    group_name = st.text_input("새 그룹 이름", placeholder="예: 반도체")
    group_symbol = st.text_input("그룹에 넣을 티커", placeholder="예: 000660.KS")
    if st.button("그룹 생성 또는 종목 추가"):
        if group_name.strip() and group_symbol.strip():
            st.session_state.groups.setdefault(group_name.strip(), [])
            if group_symbol.strip().upper() not in st.session_state.groups[group_name.strip()]:
                st.session_state.groups[group_name.strip()].append(group_symbol.strip().upper())
    for name, symbols in st.session_state.groups.items():
        with st.expander(f"{name} ({len(symbols)})"):
            st.write(", ".join(symbols) if symbols else "종목 없음")

# --------------------------- PAGE: SCREENER ---------------------------
elif page == "시장 스크리너":
    st.markdown("## 시장 스크리너")
    st.caption("Yahoo Finance에서 제공하는 검색 결과 기반 간단 스크리너")
    market = st.selectbox("시장", ["미국 대형주", "한국 주요 종목", "직접 티커 입력"])
    if market == "미국 대형주":
        symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "AVGO"]
    elif market == "한국 주요 종목":
        symbols = ["005930.KS", "000660.KS", "005380.KS", "035420.KS", "373220.KS", "207940.KS", "006400.KS"]
    else:
        custom = st.text_input("티커를 쉼표로 구분해 입력", "AAPL,MSFT,NVDA")
        symbols = [x.strip().upper() for x in custom.split(",") if x.strip()]
    if st.button("스크리닝 실행"):
        rows = []
        bar = st.progress(0)
        for i, sym in enumerate(symbols):
            q = cached_quote(sym)
            info = company_info(sym)
            rows.append({
                "티커": sym, "기업명": info.get("shortName", sym),
                "가격": q["price"], "등락률(%)": q["pct"],
                "시가총액": info.get("marketCap"),
                "PER": info.get("trailingPE"), "PBR": info.get("priceToBook"),
                "배당수익률": info.get("dividendYield")
            })
            bar.progress((i + 1) / max(len(symbols), 1))
        bar.empty()
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --------------------------- PAGE: FINANCIALS ---------------------------
elif page == "기업 재무":
    st.markdown("## 기업 재무 데이터")
    symbol = st.text_input("기업 티커", "MSFT").upper().strip()
    statement_type = st.selectbox("재무 데이터", ["손익계산서", "대차대조표", "현금흐름표", "분기 손익계산서", "분기 대차대조표", "분기 현금흐름표"])
    if st.button("재무 데이터 조회"):
        try:
            t = yf.Ticker(symbol)
            mapping = {
                "손익계산서": t.financials, "대차대조표": t.balance_sheet,
                "현금흐름표": t.cashflow, "분기 손익계산서": t.quarterly_financials,
                "분기 대차대조표": t.quarterly_balance_sheet,
                "분기 현금흐름표": t.quarterly_cashflow
            }
            show_table(mapping[statement_type])
        except Exception as e:
            st.error(f"조회 실패: {e}")

# --------------------------- PAGE: CALENDAR ---------------------------
elif page == "투자 캘린더":
    st.markdown("## 투자 캘린더")
    st.caption("선택한 기업의 배당 및 실적 관련 일정 정보를 조회합니다.")
    symbol = st.text_input("기업 티커", "AAPL").upper().strip()
    if st.button("일정 조회"):
        try:
            t = yf.Ticker(symbol)
            st.markdown("#### 기업 일정")
            show_table(t.calendar)
            st.markdown("#### 배당 일정 및 과거 배당")
            show_table(t.dividends.tail(30).to_frame("배당금"))
            st.markdown("#### 실적 발표일")
            show_table(t.earnings_dates)
        except Exception as e:
            st.warning(f"일정 데이터를 제공하지 않습니다: {e}")
    st.markdown("#### 주요 거시경제 일정")
    st.info("현재 버전에는 범용 중앙은행·물가·고용 이벤트 캘린더 API가 연결되어 있지 않습니다. 이 영역은 추후 공식 경제 캘린더 데이터 공급자를 연결하도록 구성했습니다.")

# --------------------------- PAGE: OPTIONS ---------------------------
elif page == "옵션 데이터":
    st.markdown("## 옵션 데이터")
    st.caption("Yahoo Finance에서 옵션 체인을 제공하는 종목만 표시됩니다.")
    symbol = st.text_input("종목 티커", "AAPL").upper().strip()
    try:
        t = yf.Ticker(symbol)
        expiries = t.options
        if not expiries:
            st.info("이 종목은 옵션 만기 데이터가 제공되지 않습니다.")
        else:
            expiry = st.selectbox("만기일", expiries)
            chain = t.option_chain(expiry)
            left, right = st.columns(2)
            with left:
                st.markdown("#### 콜 옵션")
                st.dataframe(chain.calls, use_container_width=True, hide_index=True)
            with right:
                st.markdown("#### 풋 옵션")
                st.dataframe(chain.puts, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"옵션 데이터를 불러오지 못했습니다: {e}")

# --------------------------- PAGE: INSIDERS ---------------------------
elif page == "내부자 거래":
    st.markdown("## 내부자 거래")
    symbol = st.text_input("종목 티커", "NVDA").upper().strip()
    if st.button("내부자 거래 조회"):
        try:
            t = yf.Ticker(symbol)
            st.markdown("#### 내부자 거래 내역")
            show_table(t.insider_transactions)
            st.markdown("#### 주요 내부자 보유 현황")
            show_table(t.insider_roster_holders)
        except Exception as e:
            st.warning(f"내부자 거래 데이터 조회 실패: {e}")

# --------------------------- PAGE: FILINGS ---------------------------
elif page == "공시 자료":
    st.markdown("## 기업 공시 및 제출 자료")
    symbol = st.text_input("미국 상장사 티커", "AAPL").upper().strip()
    if st.button("공시 자료 조회"):
        try:
            filings = yf.Ticker(symbol).sec_filings
            show_table(filings)
            st.caption("SEC 제출 자료는 미국 상장사 중심이며, 모든 국가의 공시를 포괄하지 않습니다.")
        except Exception as e:
            st.warning(f"공시 데이터를 제공하지 않거나 조회에 실패했습니다: {e}")
    st.markdown("#### 한국 기업 공시")
    st.info("한국 DART 공시는 금융감독원 OpenDART API 키를 연결하면 확장할 수 있습니다. 키는 Streamlit Secrets에 저장해야 합니다.")

# --------------------------- PAGE: COMMUNITY ---------------------------
elif page == "커뮤니티":
    st.markdown("## 투자 커뮤니티")
    st.caption("현재 버전은 세션 내 임시 게시판입니다. 영구 저장·계정·신고·관리 기능은 데이터베이스와 인증 시스템 연결이 필요합니다.")
    with st.form("community_form"):
        author = st.text_input("작성자", "Guest")
        title = st.text_input("제목")
        body = st.text_area("내용")
        submitted = st.form_submit_button("게시")
    if submitted and title.strip() and body.strip():
        st.session_state.community_posts.insert(0, {
            "author": author[:30], "title": title[:120],
            "body": body[:3000], "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    if not st.session_state.community_posts:
        st.info("아직 게시글이 없습니다.")
    for post in st.session_state.community_posts:
        with st.container(border=True):
            st.markdown(f"**{post['title']}**")
            st.caption(f"{post['author']} · {post['time']}")
            st.write(post["body"])

# --------------------------- PAGE: SETTINGS ---------------------------
elif page == "설정":
    st.markdown("## 설정")
    st.markdown("### 데이터 새로고침")
    st.write("시장·뉴스 데이터는 캐시를 사용해 반복 요청을 줄입니다.")
    if st.button("전체 데이터 캐시 초기화"):
        st.cache_data.clear()
        st.success("캐시를 초기화했습니다.")
        st.rerun()
    st.markdown("### 가격 알림 조건")
    with st.form("alert_form"):
        alert_symbol = st.text_input("종목 티커", "AAPL").upper().strip()
        direction = st.selectbox("조건", ["이상", "이하"])
        target = st.number_input("기준 가격", min_value=0.0, value=200.0, step=1.0)
        save_alert = st.form_submit_button("알림 조건 저장")
    if save_alert:
        st.session_state.alerts.append({
            "symbol": alert_symbol, "direction": direction, "target": target
        })
    if st.session_state.alerts:
        st.dataframe(pd.DataFrame(st.session_state.alerts), use_container_width=True, hide_index=True)
        st.caption("현재 알림은 조건 저장만 지원합니다. 백그라운드 실시간 감시·푸시 알림은 별도 서버 작업이 필요합니다.")
    st.markdown("### 플랫폼 정보")
    st.write("영크크 Global Financial Intelligence")
    st.write("시장 데이터: Yahoo Finance 연동 라이브러리")
    st.write("뉴스: Google News RSS / Yahoo Finance")

# --------------------------- DISCLAIMER ---------------------------
st.divider()
st.markdown("""
<div style="color:#718096;font-size:10px;line-height:1.6">
영크크는 금융 정보 탐색 및 교육 목적의 정보 플랫폼입니다. 표시되는 가격·뉴스·재무 데이터는
지연되거나 누락될 수 있으며, 데이터 공급자의 이용약관과 재배포 제한을 따릅니다.
이 서비스는 투자 자문, 매수·매도 추천, 주문 실행 또는 수익 보장을 제공하지 않습니다.
데이터를 투자 판단에 사용하기 전에 원천 제공자의 최신 정보를 확인하세요.
</div>
""", unsafe_allow_html=True)
