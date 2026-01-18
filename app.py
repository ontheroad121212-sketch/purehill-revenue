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
st.caption("경쟁사 최저가 매트릭스 및 가격 격차(Gap) 분석 시스템")

# 2. 데이터 불러오기 및 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 10초마다 갱신
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제]
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        
        # 가격 숫자 변환
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        
        # 수집시간 날짜 변환
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        return data.dropna(subset=['호텔명', '가격', '날짜'])
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- [사이드바 필터 구역] ---
        st.sidebar.header("🔍 기본 분석 필터")
        
        # 1. 분석 날짜 선택
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 날짜 선택 (복수 가능)", 
                                               options=all_dates, 
                                               default=all_dates if all_dates else [])
        
        # 2. 비교 호텔 선택 (지배인님의 13개 호텔 리스트 반영)
        all_hotels = sorted(df['호텔명'].unique())
        default_hotels = [h for h in all_hotels if "앰버" in h] + ["신라호텔", "그랜드하얏트", "파르나스", "롯데호텔"]
        default_hotels = [h for h in default_hotels if h in all_hotels]
        
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔 선택", 
                                                options=all_hotels, 
                                                default=default_hotels if default_hotels else all_hotels[:5])

        # 3. 상세 솔팅 (객실 및 채널)
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 정밀 솔팅")
        temp_f_df = df[df['호텔명'].isin(selected_hotels)]
        selected_rooms = st.sidebar.multiselect("🛏️ 특정 객실 타입만 보기", options=sorted(temp_f_df['객실타입'].unique()))
        selected_channels = st.sidebar.multiselect("📱 특정 판매처만 보기", options=sorted(df['판매처'].unique()))

        # --- 데이터 필터링 적용 ---
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_rooms: f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels: f_df = f_df[f_df['판매처'].isin(selected_channels)]

        if not f_df.empty:
            # ---------------------------------------------------------
            # 1. 경쟁사 최저가 비교 매트릭스 (지배인님 요청 사항)
            # ---------------------------------------------------------
            st.subheader("🎯 시장 최저가 요약 매트릭스")
            
            # 날짜별 호텔 최저가 피벗
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            
            # 최저가 하이라이트 스타일 함수
            def highlight_min(s):
                is_min = s == s.min()
                return ['background-color: #FFEBEE; font-weight: bold' if v else '' for v in is_min]

            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").apply(highlight_min, axis=0), 
                         use_container_width=True)
            st.caption("💡 분홍색 셀: 해당 날짜의 전체 호텔 중 최저가")

            # ---------------------------------------------------------
            # 2. 엠버퓨어힐 대비 가격 격차 (Gap Analysis)
            # ---------------------------------------------------------
            amber_keyword = "엠버"
            amber_data = f_df[f_df['호텔명'].str.contains(amber_keyword, na=False)]
            
            if not amber_data.empty:
                st.markdown("---")
                st.subheader("⚖️ 엠버퓨어힐 대비 가격 격차 (Market Gap)")
                
                # 날짜별 엠버의 최저가 추출
                amber_min_series = amber_data.groupby('날짜')['가격'].min()
                
                gap_df = pivot_df.copy()
                for date in gap_df.columns:
                    if date in amber_min_series:
                        gap_df[date] = gap_df[date] - amber_min_series[date]
                
                def color_gap(val):
                    if val < 0: return 'color: #D32F2F; font-weight: bold' # 우리보다 쌈 (위험)
                    if val > 0: return 'color: #1976D2' # 우리보다 비쌈 (양호)
                    return ''

                st.dataframe(gap_df.style.format("{:+,.0f}원", na_rep="-").applymap(color_gap), 
                             use_container_width=True)
                st.caption("💡 빨간색(-): 엠버보다 저렴한 경쟁사 / 파란색(+): 엠버보다 비싼 경쟁사")

            st.markdown("---")

            # 3. 상세 데이터 표 및 분포
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("📋 실시간 상세 요금 일람")
                st.dataframe(f_df.sort_values(['날짜', '가격'])[['날짜', '호텔명', '객실타입', '판매처', '가격']], 
                             use_container_width=True, hide_index=True)
            with col2:
                st.subheader("📊 호텔별 가격 분포")
                fig_box = px.box(f_df, x="호텔명", y="가격", color="호텔명", points="all")
                fig_box.update_layout(showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)

            # 4. 수집 트렌드 그래프
            st.subheader("📉 수집 시점별 최저가 추이")
            fig_line = px.line(f_df.sort_values('수집시간'), x='수집시간', y='가격', 
                               color='호텔명', line_dash='날짜', markers=True,
                               hover_data=['판매처', '객실타입'])
            st.plotly_chart(fig_line, use_container_width=True)

        else:
            st.warning("필터 조건에 맞는 데이터가 없습니다.")

    else:
        st.warning("구글 시트가 비어있습니다. 수집기를 먼저 가동해주세요.")

except Exception as e:
    st.error(f"대시보드 구동 중 에러 발생: {e}")
