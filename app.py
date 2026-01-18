import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="앰버 AI 지배인", layout="wide")

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.info("현재 단계: 경쟁사(그랜드 조선 제주) 요금 모니터링 화면 구현")

# 1. 날짜 선택 (오늘 기준 내일 날짜로 기본 세팅)
st.sidebar.header("조회 설정")
target_date = st.sidebar.date_input("체크인 날짜 선택", datetime.now() + timedelta(days=1))
date_str = target_date.strftime("%Y%m%d")

# 2. 네이버 호텔 바로가기 링크 생성 (그랜드 조선 제주 ID: 1335035205)
# 이 링크는 선택한 날짜에 맞게 자동으로 변합니다.
naver_url = f"https://hotels.naver.com/hotels/1335035205?checkIn={target_date.strftime('%Y-%m-%d')}&checkOut={(target_date + timedelta(days=1)).strftime('%Y-%m-%d')}&adultCnt=2"

st.subheader(f"📊 경쟁사 모니터링: 그랜드 조선 제주 ({target_date} 기준)")
st.markdown(f"[👉 직접 네이버 호텔에서 요금 확인하기]({naver_url})")

# 3. 요금 표시 구역 (임시 데이터 - 다음 스텝에서 자동 수집 연결)
st.write("---")
st.write("💡 **실시간 요금 현황** (아직은 자동 수집 전이라 예시 숫자가 표시됩니다)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="최저가 요금", value="285,000원", delta="-2,500원")
with col2:
    st.metric(label="아고다(Agoda)", value="290,000원")
with col3:
    st.metric(label="트립닷컴(Trip.com)", value="288,000원")
with col4:
    st.metric(label="트립비토즈(Tripbitoz)", value="285,000원")

# 4. 데이터 저장용 표
data = {
    "수집시간": [datetime.now().strftime("%H:%M:%S")],
    "최저가": ["285,000"],
    "아고다": ["290,000"],
    "트립닷컴": ["288,000"],
    "트립비토즈": ["285,000"]
}
df = pd.DataFrame(data)
st.table(df)

# 5. 향후 자동화될 부분 안내
st.warning("⚠️ 다음 스텝: 위 '가격'들을 사람 대신 컴퓨터가 버튼 하나로 긁어오게(Crawling) 만들 예정입니다.")
