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
    .stDataFrame { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("멀티 날짜 비교 및 정밀 데이터 솔팅 시스템")

# 2. 데이터 불러오기 및 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 실시간 확인을 위해 10초마다 갱신
def load_data():
    try:
        # 구글 시트 데이터 로드
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제]
        # 1. 호텔명과 날짜: 공백 제거
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        
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
        # --- [사이드바 필터 구역] ---
        st.sidebar.header("🔍 기본 필터")
        
        # 1. 날짜 멀티 선택
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 투숙 예정일 선택 (복수 선택 가능)", 
                                               options=all_dates, 
                                               default=[all_dates[-1]] if all_dates else [])
        
        # 2. 호텔 멀티 선택
        all_hotels = sorted(df['호텔명'].unique())
        default_hotels = [h for h in all_hotels if "엠버" in h] + ["신라호텔", "그랜드하얏트", "파르나스"]
        default_hotels = [h for h in default_hotels if h in all_hotels]
        
        selected_hotels = st.sidebar.multiselect("🏨 비교 호텔 선택", 
                                                options=all_hotels, 
                                                default=default_hotels if default_hotels else all_hotels[:4])

        # 3. 상세 솔팅 필터 (객실 및 판매처)
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 정밀 솔팅 (선택 사항)")
        
        # 선택된 호텔의 객실들만 추출
        temp_filter_df = df[df['호텔명'].isin(selected_hotels)]
        all_rooms = sorted(temp_filter_df['객실타입'].unique())
        selected_rooms = st.sidebar.multiselect("🛏️ 특정 객실 타입만 보기", 
                                               options=all_rooms,
                                               help="비워두면 선택한 호텔의 모든 객실을 보여줍니다.")
        
        all_channels = sorted(df['판매처'].unique())
        selected_channels = st.sidebar.multiselect("📱 특정 판매처만 보기", 
                                                  options=all_channels,
                                                  help="비워두면 모든 채널을 보여줍니다.")

        # --- 데이터 필터링 적용 ---
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        
        if selected_rooms:
            f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels:
            f_df = f_df[f_df['판매처'].isin(selected_channels)]

        if not f_df.empty:
            # --- 1. 실시간 요약 지표 (솔팅 기준) ---
            st.subheader("📊 선택 데이터 요약")
            m_col1, m_col2, m_col3 = st.columns(3)
            
            with m_col1:
                # 엠버 최저가 (솔팅된 필터 내에서)
                amber_val = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
                if not amber_val.empty:
                    st.metric("선택 범위 내 엠버 최저가", f"{amber_val['가격'].min():,.0f}원")
                else:
                    st.metric("선택 범위 내 엠버", "데이터 없음")
            
            with m_col2:
                st.metric("비교 그룹 최저가", f"{f_df['가격'].min():,.0f}원")
            
            with m_col3:
                st.metric("비교 그룹 평균가", f"{f_df['가격'].mean():,.0f}원")

            st.markdown("---")

            # --- 2. 상세 요금 일람표 (지배인님 요청 사항) ---
            st.subheader("📋 상세 요금 데이터 (날짜/가격순 솔팅)")
            # 날짜별, 호텔별, 가격 낮은순 정렬
            display_df = f_df.sort_values(['날짜', '호텔명', '가격'], ascending=[True, True, True])
            
            st.dataframe(
                display_df[['날짜', '호텔명', '객실타입', '판매처', '가격', '수집시간']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # --- 3. 가격 변동 추이 그래프 ---
            st.subheader("📈 가격 변동 히스토리 (수집 시점별)")
            # 여러 날짜를 비교할 수 있도록 날짜를 심볼로 구분
            fig_trend = px.line(f_df.sort_values('수집시간'), 
                                x='수집시간', y='가격', color='호텔명', symbol='날짜',
                                markers=True, hover_data=['객실타입', '판매처'],
                                title="솔팅된 호텔/객실/채널 기반 가격 트렌드")
            
            st.plotly_chart(fig_trend, use_container_width=True)

            # --- 4. 원본 데이터 다운로드 ---
            with st.expander("📥 전체 수집 데이터 확인 및 백업"):
                st.write(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("데이터 다운로드 (CSV)", data=csv, file_name=f"amber_data_export.csv", mime='text/csv')

        else:
            st.warning("선택하신 조건(날짜, 호텔, 객실, 채널)에 맞는 데이터가 시트에 없습니다. 필터를 조정해 주세요.")
            st.info(f"현재 시트에 있는 날짜: {df['날짜'].unique()}")
            st.info(f"현재 시트에 있는 호텔: {df['호텔명'].unique()}")

    else:
        st.warning("구글 시트에서 불러올 데이터가 없습니다. 수집기를 먼저 가동해 주세요.")

except Exception as e:
    st.error(f"대시보드 구동 중 에러 발생: {e}")
