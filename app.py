import io
from datetime import date

import pandas as pd
import streamlit as st

# QR library is optional so the main app can still load if it is missing.
try:
    import qrcode
except ImportError:
    qrcode = None

st.set_page_config(
    page_title="스마트 소비 분석",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {padding: .55rem .7rem .6rem !important; max-width: 1050px;}
    h1 {font-size: 1.4rem !important; margin: 0 0 .1rem 0 !important;}
    h2, h3 {font-size: 1rem !important; margin: .25rem 0 !important;}
    p, label {font-size: .83rem !important;}
    div[data-testid="stMetric"] {
        padding: .35rem .5rem;
        border-radius: 10px;
        background: rgba(30, 150, 90, .09);
    }
    div[data-testid="stMetricValue"] {font-size: 1.1rem !important;}
    div[data-testid="stVerticalBlock"] {gap: .4rem !important;}
    div.stButton > button, div.stDownloadButton > button {
        min-height: 2.1rem;
        padding: .25rem .5rem;
    }
    div[data-testid="stForm"] {padding: .55rem; border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORIES = [
    "식비", "카페·간식", "교통", "쇼핑·의류",
    "생활용품", "문화·여가", "교육", "기타",
]
CONSUMPTION_TYPES = ["필요한 소비", "원하는 소비"]

if "records" not in st.session_state:
    st.session_state.records = []

st.title("💳 스마트 소비 분석")
st.caption("소비를 기록하고 예산과 소비 습관을 한눈에 확인하세요.")

# Budget and QR address
budget_col, qr_col = st.columns([1, 1.35])
with budget_col:
    budget = st.number_input(
        "이번 달 예산 (원)", min_value=0, value=300000, step=10000
    )
with qr_col:
    app_url = st.text_input(
        "앱 QR 주소 (배포 후 입력)",
        placeholder="https://your-app.streamlit.app",
    )

records = st.session_state.records
total = sum(record["금액"] for record in records)
necessary_total = sum(
    record["금액"]
    for record in records
    if record["소비 성격"] == "필요한 소비"
)
optional_total = total - necessary_total
remaining = budget - total
usage_percent = total / budget * 100 if budget > 0 else 0

metric_cols = st.columns(4)
metric_cols[0].metric("총 지출", f"{total:,.0f}원")
metric_cols[1].metric("남은 예산", f"{remaining:,.0f}원")
metric_cols[2].metric("필요한 소비", f"{necessary_total:,.0f}원")
metric_cols[3].metric("원하는 소비", f"{optional_total:,.0f}원")

if budget > 0:
    st.progress(
        min(max(usage_percent / 100, 0.0), 1.0),
        text=f"예산 사용률 {usage_percent:.1f}%",
    )
    if total > budget:
        st.error(
            f"예산을 {total - budget:,.0f}원 초과했어요. 추가 지출을 점검해 보세요."
        )
    elif usage_percent >= 80:
        st.warning("예산의 80% 이상을 사용했어요. 남은 지출을 확인해 보세요.")
else:
