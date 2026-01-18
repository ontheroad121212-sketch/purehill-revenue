import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 통합 대시보드", layout="wide")

# CSS를 이용해 가독성 및 디자인 강화
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("실시간 시장 데이터 동기화 및 가격 변동 분석 시스템")

# 2. 데이터 불러오기 및 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60) # 즉각적인 확인을 위해 캐시 유지시간을 1분으로 단축
def load_data():
    # 구글 시트 데이터 읽기
    data = pd.read_csv(URL, encoding='utf-8-sig')
    
    # [핵심 보완] 데이터 정제 로직
    # 1. 호텔명과 날짜의 앞뒤 공백 제거 (필터링 실패 방지)
    data['호텔명'] = data['호텔명'].astype(str).str.strip()
    data['날짜'] = data['날짜'].astype(str).str.strip()
    
    # 2. 가격 컬럼에서 콤마(,) 제거 후 숫자로 변환
    data['가격'] = data['가격'].astype(str).str.replace(',', '')
    data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
    
    # 3. 수집시간을 날짜형으로 변환
    data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
    
    # 데이터가 없는 행(NaN) 제거
    data = data.dropna(subset=['호텔명', '가격', '날짜'])
    
    return data

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 구역 ---
        st.sidebar.header("🔍 분석 필터")
        
        # 투숙 날짜 선택
        all_target_dates = sorted(df['날짜'].unique())
        selected_date = st.sidebar.selectbox("📅 투숙 예정일 선택", options=all_target_dates)
        
        # 비교 호텔 선택 (기본값 설정 보강)
        all_hotels = sorted(df['호텔명'].unique())
        
        # 엠버퓨어힐이 리스트에 있는지 확인 후 기본 선택값으로 지정
        default_selection = [h for h in all_hotels if "엠버" in h] + ["신라호텔", "그랜드하얏트", "파르나스"]
        # 리스트에 없는 호텔은 제외
        default_selection = [h for h in default_selection if h in all_hotels]

        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=default_selection if default_selection else all_hotels[:4]
        )

        # --- 데이터 필터링 수행 ---
        # 1. 전체 히스토리용 (그래프용)
        history_df = df[(df['날짜'] == selected_date) & (df['호텔명'].isin(selected_hotels))]
        
        # 2. 실시간 현황용 (가장 최근 수집 시간 기준)
        if not history_df.empty:
            latest_time = history_df['수집시간'].max()
            current_df = history_df[history_df['수집시간'] == latest_time]
            
            # --- 메인 현황 요약 ---
            st.subheader(f"📊 {selected_date} 투숙분 - 실시간 요약")
            st.info(f"마지막 데이터 수집 시점: {latest_update if 'latest_update' in locals() else latest_time}")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                # 엠버퓨어힐 가격 추출 (이름 포함 여부로 한 번 더 체크)
                amber_price = current_df[current_df['호텔명'].str.contains("엠버", na=False)]['가격'].min()
                if not pd.isna(amber_price):
                    st.metric("엠버퓨어힐 최저가", f"{amber_price:,.0f}원")
                else:
                    st.metric("엠버퓨어힐 최저가", "데이터 없음")
            
            with m_col2:
                st.metric("선택 그룹 최저가", f"{current_df['가격'].min():,.0f}원")
            with m_col3:
                st.metric("선택 그룹 평균가", f"{current_df['가격'].mean():,.0f}원")

            st.markdown("---")

            # --- 가격 변동 추이 그래프 ---
            st.subheader("📉 수집 시점별 가격 변동 히스토리")
            trend_data = history_df.groupby(['수집시간', '호텔명'])['가격'].min().reset_index()
            
            fig_trend = px.line(trend_data, x='수집시간', y='가격', color='호텔명', markers=True,
                                title=f"{selected_date} 요금 변동 추이 (누적 데이터)")
            st.plotly_chart(fig_trend, use_container_width=True)

            st.markdown("---")

            # --- 상세 요금표 ---
            st.subheader("📋 상세 요금 비교 (최신 수집본)")
            display_df = current_df[['호텔명', '객실타입', '판매처', '가격', '수집시간']].sort_values('가격')
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # --- 데이터 다운로드 기능 ---
            with st.expander("📥 전체 수집 데이터 보기 및 저장"):
                st.write(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("CSV로 내보내기", data=csv, file_name=f"amber_report_{selected_date}.csv", mime='text/csv')
        else:
            st.warning(f"'{selected_date}' 날짜에 선택하신 호텔의 데이터가 없습니다. 사이드바 설정을 확인해 주세요.")

    else:
        st.warning("구글 시트에 연결되었으나 수집된 데이터가 없습니다. Collector.py를 실행해 주세요.")

except Exception as e:
    st.error(f"데이터를 읽어오는 중 오류가 발생했습니다: {e}")
