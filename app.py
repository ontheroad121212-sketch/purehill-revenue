import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 전략 대시보드", layout="wide")

# 가독성과 직관성을 극대화하는 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1a1c1e; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("실시간 시장 데이터 동기화 및 3초 전략 판단 시스템")

# 2. 데이터 로드 및 정제
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        # 데이터 정밀 정제
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
        st.sidebar.header("🔍 분석 필터 설정")
        
        # 1. 분석 대상 날짜 선택 (멀티 선택)
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 날짜", options=all_dates, default=all_dates if all_dates else [])
        
        # 2. 지배인님의 13개 호텔 전체 리스트 반영
        all_hotels = sorted(df['호텔명'].unique())
        default_hotels = [
            "엠버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", 
            "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", 
            "조선힐스위트", "메종글래드", "그랜드조선제주"
        ]
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔", options=all_hotels, default=[h for h in default_hotels if h in all_hotels])

        # 3. 상세 솔팅 (객실 및 채널)
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 정밀 솔팅")
        temp_filter = df[df['호텔명'].isin(selected_hotels)]
        selected_rooms = st.sidebar.multiselect("🛏️ 특정 객실 타입만 보기", options=sorted(temp_filter['객실타입'].unique()))
        selected_channels = st.sidebar.multiselect("📱 특정 판매처만 보기", options=sorted(df['판매처'].unique()))

        # 필터링 적용 데이터 생성
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_rooms: f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels: f_df = f_df[f_df['판매처'].isin(selected_channels)]

        if not f_df.empty:
            # ---------------------------------------------------------
            # 1. 상단 핵심 지표 (오늘의 핵심 지표 카드)
            # ---------------------------------------------------------
            st.subheader("🚀 실시간 시장 지위 요약")
            amber_data = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                if not amber_data.empty:
                    latest_amber = amber_data.sort_values('수집시간').iloc[-1]
                    st.metric("엠버 현재 최저가", f"{latest_amber['가격']:,.0f}원", help=f"객실: {latest_amber['객실타입']}")
                else:
                    st.metric("엠버 현재 최저가", "데이터 없음")
            
            with m_col2:
                market_min_idx = f_df['가격'].idxmin()
                market_min_val = f_df.loc[market_min_idx, '가격']
                market_min_hotel = f_df.loc[market_min_idx, '호텔명']
                st.metric("시장 전체 최저가", f"{market_min_val:,.0f}원", help=f"최저가 호텔: {market_min_hotel}")

            with m_col3:
                market_avg = f_df['가격'].mean()
                if not amber_data.empty:
                    diff_ratio = ((latest_amber['가격'] - market_avg) / market_avg) * 100
                    st.metric("시장 평균가 대비", f"{diff_ratio:+.1f}%")
                else:
                    st.metric("시장 평균가 대비", "-")

            with m_col4:
                top_channel = f_df['판매처'].value_counts().idxmax()
                st.metric("활성 1위 채널", top_channel)

            st.markdown("---")

            # ---------------------------------------------------------
            # 2. 신호등 가격 매트릭스 (직관적 비교 표)
            # ---------------------------------------------------------
            st.subheader("🚦 일자별 호텔 최저가 매트릭스 (신호등)")
            
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            
            # 스타일 함수: 우리보다 3만원 이상 싸면 빨강, 0~3만 원 사이면 노랑
            def color_signal(val):
                if pd.isna(val) or amber_data.empty: return ''
                amber_ref = amber_data['가격'].min() 
                diff = val - amber_ref
                if diff < -30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold' 
                if diff < 0: return 'background-color: #fff3cd; color: #856404;' 
                return 'background-color: #d4edda; color: #155724;' 

            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_signal), 
                         use_container_width=True)
            st.caption("💡 신호등: 빨강(경쟁사 위협가) / 노랑(경쟁사 약우세) / 초록(엠버 우세)")

            st.markdown("---")

            # ---------------------------------------------------------
            # 3. 엠버 전용 분석 존 (주력 객실 3종 분석)
            # ---------------------------------------------------------
            col_a, col_b = st.columns([3, 2])
            
            with col_a:
                st.subheader("💎 엠버 주력 객실별 채널 분포 (Heatmap)")
                if not amber_data.empty:
                    # 힐엠버, 힐파인, 그린밸리 필터링
                    amber_pivot = amber_data.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
                    fig_heat = px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto")
                    fig_heat.update_layout(height=400)
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.info("엠버퓨어힐 데이터를 수집해주세요.")

            with col_b:
                st.subheader("📊 호텔별 요금 분포 범위")
                fig_box = px.box(f_df, x="호텔명", y="가격", color="호텔명")
                fig_box.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_box, use_container_width=True)

            # ---------------------------------------------------------
            # 4. 가격 변동 추이 및 상세 데이터
            # ---------------------------------------------------------
            st.subheader("📉 수집 시점별 가격 히스토리")
            fig_line = px.line(f_df.sort_values('수집시간'), x='수집시간', y='가격', 
                               color='호텔명', line_dash='날짜', markers=True,
                               hover_data=['판매처', '객실타입'])
            st.plotly_chart(fig_line, use_container_width=True)

            with st.expander("📋 상세 데이터 로그 확인"):
                st.dataframe(f_df.sort_values(['날짜', '수집시간'], ascending=[True, False]), 
                             use_container_width=True, hide_index=True)

        else:
            st.warning("선택된 필터 조건에 데이터가 없습니다.")
    else:
        st.error("데이터가 비어있습니다. 수집기(Collector.py)를 실행해주세요.")

except Exception as e:
    st.error(f"대시보드 에러: {e}")
