import io
from datetime import date

import pandas as pd
import qrcode
import streamlit as st

st.set_page_config(
    page_title="스마트 소비 분석",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 초록색 중심의 금융 앱 스타일 + 컴팩트한 단일 대시보드
st.markdown(
    """
    <style>
    :root { --main-green: #16845b; }
    .stApp { background: #f6faf7; }
    [data-testid="stHeader"] { background: rgba(246,250,247,.9); }
    .block-container { max-width: 1050px; padding: .65rem .8rem .8rem !important; }
    h1 { color: #126b4b; font-size: 1.55rem !important; margin: 0 0 .1rem 0 !important; }
    h2, h3 { color: #185d45; font-size: 1.02rem !important; margin: .25rem 0 !important; }
    [data-testid="stMetric"] { background: #e8f4ed; border: 1px solid #d4e9dc; padding: .45rem .6rem; border-radius: 12px; }
    [data-testid="stMetricLabel"] { color: #47735d !important; }
    [data-testid="stMetricValue"] { color: #126b4b !important; font-size: 1.2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: .42rem !important; }
    div[data-testid="stForm"] { background: white; border: 1px solid #dcebe1; border-radius: 12px; padding: .65rem; }
    div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
        border-radius: 9px; min-height: 2.25rem; font-weight: 600;
    }
    div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: #16845b; border-color: #16845b;
    }
    [data-testid="stCaptionContainer"] { color: #668071; }
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORIES = ["식비", "카페·간식", "교통", "쇼핑·의류", "생활용품", "문화·여가", "교육", "기타"]
SPENDING_TYPES = ["필수 소비", "선택 소비"]

if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 300000

st.title("💚 스마트 소비 분석")
st.caption("나의 소비를 기록하고 예산을 계획적으로 관리해 보세요.")

# 상단 예산 설정
budget_col, month_col = st.columns([1.35, 1])
with budget_col:
    budget = st.number_input(
        "이번 달 예산 (원)", min_value=0, max_value=100000000,
        value=int(st.session_state.monthly_budget), step=10000,
        help="이번 달에 사용할 전체 예산을 입력하세요.",
    )
    st.session_state.monthly_budget = int(budget)
with month_col:
    selected_month = st.selectbox(
        "분석 월", options=[date.today().strftime("%Y-%m"),
                         (date.today().replace(day=1) - pd.Timedelta(days=1)).strftime("%Y-%m")],
        index=0,
    )

all_records = st.session_state.transactions
month_records = [r for r in all_records if r["date"].startswith(selected_month)]
spent = sum(r["amount"] for r in month_records)
remaining = int(budget) - spent
essential_total = sum(r["amount"] for r in month_records if r["spending_type"] == "필수 소비")
optional_total = spent - essential_total
budget_rate = spent / budget if budget else 0

# 주요 지표
metric1, metric2, metric3 = st.columns(3)
metric1.metric("이번 달 총지출", f"{spent:,.0f}원")
metric2.metric("남은 예산", f"{remaining:,.0f}원")
metric3.metric("예산 사용률", f"{budget_rate * 100:.1f}%")
if budget > 0:
    st.progress(min(max(budget_rate, 0.0), 1.0), text="월 예산 사용 현황")
    if remaining < 0:
        st.error(f"예산을 {abs(remaining):,}원 초과했어요. 추가 지출을 점검해 보세요.")
    elif budget_rate >= 0.8:
        st.warning("예산의 80% 이상을 사용했어요. 남은 예산을 확인해 보세요.")
else:
    st.info("예산을 입력하면 남은 금액과 사용률을 계산해 드려요.")

left, right = st.columns([1, 1.2], gap="medium")

with left:
    st.subheader("＋ 소비 기록")
    with st.form("transaction_form", clear_on_submit=True):
        item_name = st.text_input("구매 항목", placeholder="예: 점심 식사, 운동화")
        amount_col, category_col = st.columns(2)
        amount = amount_col.number_input("금액 (원)", min_value=0, max_value=100000000, value=0, step=500)
        category = category_col.selectbox("카테고리", CATEGORIES)
        type_col, date_col = st.columns(2)
        spending_type = type_col.selectbox("소비 유형", SPENDING_TYPES)
        purchase_date = date_col.date_input("구매 날짜", value=date.today())
        memo = st.text_input("메모 (선택)", placeholder="예: 할인 구매")
        submitted = st.form_submit_button("소비 내역 추가", use_container_width=True, type="primary")
        if submitted:
            if not item_name.strip():
                st.warning("구매 항목을 입력해 주세요.")
            elif amount <= 0:
                st.warning("금액은 1원 이상 입력해 주세요.")
            else:
                st.session_state.transactions.append({
                    "date": purchase_date.isoformat(),
                    "name": item_name.strip(),
                    "category": category,
                    "spending_type": spending_type,
                    "amount": int(amount),
                    "memo": memo.strip(),
                })
                st.rerun()

    st.subheader("📊 소비 구성")
    if month_records:
        category_df = pd.DataFrame(month_records).groupby("category")["amount"].sum().sort_values(ascending=False)
        st.bar_chart(category_df, height=170, color="#16845b")
        type_col1, type_col2 = st.columns(2)
        type_col1.metric("필수 소비", f"{essential_total:,.0f}원")
        type_col2.metric("선택 소비", f"{optional_total:,.0f}원")
        if optional_total > essential_total:
            st.caption("선택 소비가 필수 소비보다 많아요. 구매 전 필요성을 확인해 보세요.")
        else:
            st.caption("필수 소비가 선택 소비보다 많아요.")
    else:
        st.caption("선택한 달의 소비를 등록하면 분석 그래프가 표시돼요.")

with right:
    st.subheader("🧾 소비 내역")
    if month_records:
        display_records = sorted(month_records, key=lambda r: r["date"], reverse=True)
        for index, record in enumerate(display_records[:4]):
            row_left, row_right = st.columns([5, 1])
            row_left.markdown(f"**{record['name']}** · {record['amount']:,}원")
            row_left.caption(f"{record['date']} · {record['category']} · {record['spending_type']}")
            # 같은 항목명이 있어도 원본 전체 기록에서 정확히 삭제
            if row_right.button("삭제", key=f"del_{all_records.index(record)}_{index}"):
                st.session_state.transactions.remove(record)
                st.rerun()
        if len(month_records) > 4:
            st.caption(f"최근 4건 표시 · 선택한 달 전체 {len(month_records)}건")
    else:
        st.info("아직 등록된 소비 내역이 없어요.")

    if all_records:
        export_df = pd.DataFrame(all_records).rename(columns={
            "date": "날짜", "name": "항목", "category": "카테고리",
            "spending_type": "소비 유형", "amount": "금액(원)", "memo": "메모",
        })
        st.download_button(
            "전체 소비 내역 다운로드 (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="smart_consumption.csv", mime="text/csv", use_container_width=True,
        )

    with st.expander("📱 앱 접속 QR 코드"):
        app_url = st.text_input("배포된 Streamlit 앱 주소", placeholder="https://내앱이름.streamlit.app")
        if app_url.strip().startswith(("https://", "http://")):
            qr_buffer = io.BytesIO()
            qrcode.make(app_url.strip()).save(qr_buffer, format="PNG")
            qr_bytes = qr_buffer.getvalue()
            st.image(qr_bytes, width=145, caption="휴대폰 카메라로 스캔")
            st.download_button("QR 이미지 저장", qr_bytes, file_name="smart_consumption_qr.png", mime="image/png")
        elif app_url.strip():
            st.caption("주소는 https:// 또는 http://로 시작해야 해요.")

st.caption("데이터 안내: 현재 기록은 앱 세션 동안 유지됩니다. 앱을 다시 열어도 계속 보관하려면 별도 데이터베이스 연결이 필요합니다.")
