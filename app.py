import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 디자인 (가로로 넓게 보기)
st.set_page_config(page_title="앰버 AI 지배인 통합 대시보드", layout="wide")

# 가독성을 높이기 위한 CSS 디자인
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("실시간 시장 데이터 동기화 및 가격 변동 분석 시스템")

# 2. 데이터 불러오기 및 정제 함수
# 지배인님의 구글 시트 ID와 URL
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=30) # 30초마다 데이터 갱신 (테스트 중엔 짧게 설정)
def load_data():
    try:
        # 구글 시트 데이터 로드
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제 로직 시작]
        # 1. 호텔명과 날짜: 모든 띄어쓰기를 제거하고 양 끝 공백도 지움 (비교 정확도 100%)
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        
        # 2. 가격: 문자열로 바꾼 뒤 콤마(,)와 '원' 등 숫자 이외의 것을 지우고 숫자로 변환
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        
        # 3. 수집시간: 날짜 형식으로 변환 (시간순 정렬용)
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        # 유효하지 않은 행(데이터 누락) 제거
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 구역 ---
        st.sidebar.header("🔍 분석 필터")
        
        # 투숙 날짜 선택
        all_target_dates = sorted(df['날짜'].unique())
        selected_date = st.sidebar.selectbox("📅 투숙 예정일 선택", options=all_target_dates)
        
        # 비교 호텔 선택
        all_hotels = sorted(df['호텔명'].unique())
        
        # 엠버퓨어힐(또는 엠버 포함)을 기본으로 선택하도록 설정
        default_selection = [h for h in all_hotels if "엠버" in h] + ["신라호텔", "그랜드하얏트", "파르나스"]
        default_selection = [h for h in default_selection if h in all_hotels]

        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=default_selection if default_selection else all_hotels[:4]
        )

        # --- 데이터 필터링 ---
        # 1. 선택한 투숙 날짜와 선택한 호텔들 전체 히스토리
        history_df = df[(df['날짜'] == selected_date) & (df['호텔명'].isin(selected_hotels))]
        
        if not history_df.empty:
            # 2. 실시간 현황 (가장 최근 수집 시간 기준)
            latest_time = history_df['수집시간'].max()
            current_df = history_df[history_df['수집시간'] == latest_time]
            
            # --- 메인 현황 요약 카드 ---
            st.subheader(f"📊 {selected_date} 투숙분 - 실시간 요약")
            st.info(f"마지막 데이터 수집 시점: {latest_time}")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                # '엠버'가 포함된 호텔 데이터 추출
                amber_df = current_df[current_df['호텔명'].str.contains("엠버", na=False)]
                if not amber_df.empty:
                    amber_min = amber_df['가격'].min()
                    st.metric("엠버퓨어힐 최저가", f"{amber_min:,.0f}원")
                else:
                    st.metric("엠버퓨어힐 최저가", "데이터 없음")
            
            with m_col2:
                st.metric("선택 그룹 최저가", f"{current_df['가격'].min():,.0f}원")
            with m_col3:
                st.metric("선택 그룹 평균가", f"{current_df['가격'].mean():,.0f}원")

            st.markdown("---")

            # --- 가격 변동 추이 그래프 (누적 데이터 활용) ---
            st.subheader("📈 수집 시점별 가격 변동 히스토리")
            # 수집 시점별, 호텔별 최저가 추이 요약
            trend_data = history_df.groupby(['수집시간', '호텔명'])['가격'].min().reset_index()
            
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='수집시간', y='가격', color='호텔명', markers=True,
                                    title=f"'{selected_date}' 투숙 요금의 수집 날짜별 변동")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.write("변동 추이를 표시할 데이터가 부족합니다.")

            st.markdown("---")

            # --- 상세 요금 비교 표 (최신 기준) ---
            st.subheader("📋 상세 요금 비교 (최신 수집본)")
            display_df = current_df[['호텔명', '객실타입', '판매처', '가격', '수집시간']].sort_values('가격')
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # --- 데이터 백업/다운로드 ---
            with st.expander("📥 시트 원본 데이터 확인 및 CSV 다운로드"):
                st.write(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("전체 데이터 다운로드", data=csv, file_name=f"amber_full_report.csv", mime='text/csv')

        else:
            st.warning(f"'{selected_date}' 날짜에 선택하신 호텔의 데이터가 시트에 없습니다. 사이드바 설정을 확인해 주세요.")
            # 진단용: 시트에 실제 들어있는 데이터 이름들을 보여줌
            st.info(f"현재 시트에 있는 전체 날짜: {df['날짜'].unique()}")
            st.info(f"현재 시트에 있는 전체 호텔: {df['호텔명'].unique()}")

    else:
        st.warning("구글 시트가 비어 있거나 데이터를 읽을 수 없습니다. 수집기(Collector.py)를 실행해 주세요.")

except Exception as e:
    st.error(f"대시보드 실행 중 오류 발생: {e}")
