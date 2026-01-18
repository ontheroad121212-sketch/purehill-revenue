import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 통합 대시보드", layout="wide")

# CSS를 이용해 가독성 높이기
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("제주 주요 경쟁사 실시간 요금 모니터링 시스템")

# 2. 데이터 불러오기
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=600) # 10분마다 데이터 새로고침
def load_data():
    data = pd.read_csv(URL, encoding='utf-8-sig')
    # 가격 컬럼 숫자형 변환 (혹시 모를 에러 방지)
    data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
    return data

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 구역 ---
        st.sidebar.header("🔍 분석 필터")
        
        # 날짜 선택
        all_dates = sorted(df['날짜'].unique())
        selected_date = st.sidebar.selectbox("📅 조회 날짜", options=all_dates, index=0)
        
        # 호텔 선택 (멀티 선택 가능)
        all_hotels = df['호텔명'].unique()
        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=["엠버퓨어힐", "신라호텔", "그랜드하얏트", "파르나스"]
        )
        
        # 데이터 필터링
        filtered_df = df[(df['날짜'] == selected_date) & (df['호텔명'].isin(selected_hotels))]
        
        # --- 메인 화면 구역 ---
        
        # 1. 주요 지표 (선택한 호텔들 중 최저가 정보)
        st.subheader(f"📊 {selected_date} 요약 현황")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        with m_col1:
            purehill_min = df[(df['호텔명'] == '엠버퓨어힐') & (df['날짜'] == selected_date)]['가격'].min()
            if pd.isna(purehill_min):
                st.metric("엠버퓨어힐 최저가", "데이터 없음")
            else:
                st.metric("엠버퓨어힐 최저가", f"{purehill_min:,.0f}원")
                
        with m_col2:
            market_min = filtered_df['가격'].min()
            st.metric("선택 그룹 최저가", f"{market_min:,.0f}원")
            
        with m_col3:
            market_avg = filtered_df['가격'].mean()
            st.metric("선택 그룹 평균가", f"{market_avg:,.0f}원")
            
        with m_col4:
            st.metric("수집된 상품 수", f"{len(filtered_df)}개")

        st.markdown("---")

        # 2. 그래프 분석
        g_col1, g_col2 = st.columns([2, 1])
        
        with g_col1:
            st.subheader("💡 호텔별 요금 비교")
            # 호텔별 최저가 기준 차트
            hotel_min_df = filtered_df.groupby('호텔명')['가격'].min().reset_index().sort_values('가격')
            fig_bar = px.bar(hotel_min_df, x='호텔명', y='가격', color='호텔명', 
                             text_auto=',.0f', title="호텔별 최저가 비교 (낮은 순)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with g_col2:
            st.subheader("🏢 판매처 비중")
            fig_pie = px.pie(filtered_df, names='판매처', title="판매처별 상품 분포")
            st.plotly_chart(fig_pie, use_container_width=True)

        # 3. 상세 요금표
        st.subheader("📋 실시간 상세 요금표")
        # 보기 좋게 컬럼 재정렬
        display_df = filtered_df[['호텔명', '객실타입', '판매처', '가격', '수집시간']].sort_values('가격')
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # 4. 전체 데이터 익스팬더
        with st.expander("📥 전체 데이터 보기 및 다운로드"):
            st.write(df)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("CSV 다운로드", data=csv, file_name=f"amber_ai_data_{selected_date}.csv", mime='text/csv')

    else:
        st.warning("구글 시트에 데이터가 없습니다. Collector.py를 실행해 주세요.")

except Exception as e:
    st.error(f"데이터 연결 중 오류가 발생했습니다: {e}")
