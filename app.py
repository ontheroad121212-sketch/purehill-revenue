import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="앰버 AI 지배인 통합 대시보드", layout="wide")

# 가독성을 위한 CSS
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("데이터 누적을 통한 시장 가격 변동 추적 시스템")

# 2. 데이터 불러오기
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    data = pd.read_csv(URL, encoding='utf-8-sig')
    data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
    # 수집시간을 날짜형으로 변환 (시간순 정렬을 위해 필수)
    data['수집시간'] = pd.to_datetime(data['수집시간'])
    return data

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 ---
        st.sidebar.header("🔍 분석 설정")
        
        # 투숙하려는 날짜 (예: 1월 24일 요금이 언제 얼마였는지 확인용)
        all_target_dates = sorted(df['날짜'].unique())
        selected_date = st.sidebar.selectbox("📅 투숙 예정일 선택", options=all_target_dates)
        
        # 비교할 호텔들
        all_hotels = df['호텔명'].unique()
        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=["엠버퓨어힐", "신라호텔", "그랜드하얏트", "파르나스"]
        )

        # --- 메인 현황 (최신 데이터 기준) ---
        # 가장 최근에 수집된 시간 찾기
        latest_update = df['수집시간'].max()
        current_df = df[(df['수집시간'] == latest_update) & (df['날짜'] == selected_date) & (df['호텔명'].isin(selected_hotels))]
        
        st.subheader(f"📊 {selected_date} 투숙분 - 실시간 요약")
        st.info(f"마지막 데이터 수집 시점: {latest_update}")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            pure_min = current_df[current_df['호텔명'] == '엠버 퓨어힐']['가격'].min()
            st.metric("엠버 퓨어힐 최저가", f"{pure_min:,.0f}원" if not pd.isna(pure_min) else "데이터 없음")
        with m_col2:
            st.metric("선택 그룹 최저가", f"{current_df['가격'].min():,.0f}원")
        with m_col3:
            st.metric("선택 그룹 평균가", f"{current_df['가격'].mean():,.0f}원")

        st.markdown("---")

        # --- 가격 변동 추이 (누적 데이터 활용) ---
        st.subheader("📈 가격 변동 히스토리")
        st.write(f"'{selected_date}' 투숙 요금이 수집 날짜별로 어떻게 변해왔는지 보여줍니다.")

        # 선택한 투숙일과 호텔들에 대한 전체 히스토리 추출
        history_df = df[(df['날짜'] == selected_date) & (df['호텔명'].isin(selected_hotels))]
        # 수집 시점별, 호텔별 최저가 요약
        trend_data = history_df.groupby(['수집시간', '호텔명'])['가격'].min().reset_index()
        
        if not trend_data.empty:
            fig_trend = px.line(trend_data, x='수집시간', y='가격', color='호텔명', markers=True,
                                title=f"{selected_date} 요금 변동 추이")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.write("추이를 표시할 누적 데이터가 부족합니다.")

        st.markdown("---")

        # --- 상세 비교 (최신 기준) ---
        st.subheader("📋 상세 요금 비교 (최신 수집본)")
        display_df = current_df[['호텔명', '객실타입', '판매처', '가격']].sort_values('가격')
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.warning("데이터가 없습니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")
