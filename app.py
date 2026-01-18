import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 디자인
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
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 실시간 확인을 위해 10초마다 갱신
def load_data():
    try:
        # 구글 시트 데이터 로드
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제]
        # 1. 호텔명과 날짜: 모든 띄어쓰기 제거 및 공백 정리
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        
        # 2. 가격: 문자열에서 콤마(,)와 '원' 제거 후 숫자로 변환
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        
        # 3. 수집시간: 날짜 형식으로 변환
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        # 데이터 누락 행 제거
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 ---
        st.sidebar.header("🔍 분석 필터")
        all_target_dates = sorted(df['날짜'].unique())
        selected_date = st.sidebar.selectbox("📅 투숙 예정일 선택", options=all_target_dates)
        
        all_hotels = sorted(df['호텔명'].unique())
        
        # 기본 선택값 설정
        default_selection = [h for h in all_hotels if "엠버" in h] + ["신라호텔", "그랜드하얏트", "파르나스"]
        default_selection = [h for h in default_selection if h in all_hotels]

        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=default_selection if default_selection else all_hotels[:4]
        )

        # --- 데이터 필터링 (가장 중요한 부분) ---
        # 해당 날짜의 모든 데이터 확보
        date_df = df[df['날짜'] == selected_date]
        
        # 1. 그래프용 전체 히스토리 (선택된 호텔들)
        history_df = date_df[date_df['호텔명'].isin(selected_hotels)]
        
        if not history_df.empty:
            # 2. 실시간 현황 (전체 데이터 중 가장 최근 수집 시점)
            total_latest_time = date_df['수집시간'].max()
            current_df = date_df[(date_df['수집시간'] == total_latest_time) & (date_df['호텔명'].isin(selected_hotels))]
            
            # --- 메인 현황 요약 카드 ---
            st.subheader(f"📊 {selected_date} 투숙분 - 실시간 요약")
            st.info(f"전체 시스템 최종 업데이트: {total_latest_time}")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            
            with m_col1:
                # [핵심 보완] 엠버퓨어힐은 최신 수집 시간과 관계없이 해당 날짜의 '가장 최근 데이터'를 강제로 찾음
                amber_only = date_df[date_df['호텔명'].str.contains("엠버", na=False)]
                if not amber_only.empty:
                    latest_amber_time = amber_only['수집시간'].max()
                    amber_min = amber_only[amber_only['수집시간'] == latest_amber_time]['가격'].min()
                    st.metric("엠버퓨어힐 최저가", f"{amber_min:,.0f}원", help=f"우리 호텔 최종 수집: {latest_amber_time}")
                else:
                    st.metric("엠버퓨어힐 최저가", "데이터 없음")
            
            with m_col2:
                # 선택된 그룹 중 최신 수집 데이터의 최저가
                market_min = current_df['가격'].min() if not current_df.empty else history_df['가격'].min()
                st.metric("선택 그룹 최저가", f"{market_min:,.0f}원")
            
            with m_col3:
                # 선택된 그룹 중 최신 수집 데이터의 평균가
                market_avg = current_df['가격'].mean() if not current_df.empty else history_df['가격'].mean()
                st.metric("선택 그룹 평균가", f"{market_avg:,.0f}원")

            st.markdown("---")

            # --- 가격 변동 추이 그래프 ---
            st.subheader("📉 수집 시점별 가격 변동 히스토리")
            trend_data = history_df.groupby(['수집시간', '호텔명'])['가격'].min().reset_index()
            fig_trend = px.line(trend_data, x='수집시간', y='가격', color='호텔명', markers=True,
                                title=f"'{selected_date}' 투숙 요금 변동 추이")
            st.plotly_chart(fig_trend, use_container_width=True)

            st.markdown("---")

            # --- 상세 요금 비교 표 ---
            st.subheader("📋 전체 수집 상세 데이터 (최신순)")
            # 날짜 내 모든 데이터를 최신 수집 순서로 정렬하여 보여줌
            display_df = date_df[date_df['호텔명'].isin(selected_hotels)].sort_values('수집시간', ascending=False)
            st.dataframe(display_df[['호텔명', '객실타입', '판매처', '가격', '수집시간']], use_container_width=True, hide_index=True)

            # --- 데이터 백업/다운로드 ---
            with st.expander("📥 시트 원본 데이터 확인 및 CSV 다운로드"):
                st.write(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("전체 데이터 다운로드", data=csv, file_name=f"amber_full_report.csv", mime='text/csv')

        else:
            st.warning(f"'{selected_date}' 날짜에 선택하신 호텔의 데이터가 없습니다.")
            st.info(f"현재 시트에 있는 날짜: {df['날짜'].unique()}")

    else:
        st.warning("데이터가 비어 있습니다. Collector.py를 실행해 주세요.")

except Exception as e:
    st.error(f"대시보드 실행 중 오류 발생: {e}")
