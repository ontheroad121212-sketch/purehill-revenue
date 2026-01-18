import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
st.caption("3초 판단 시스템: 실시간 시장 지위 및 가격 대응 전략")

# 2. 데이터 로드 및 정제
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        return data.dropna(subset=['호텔명', '가격', '날짜'])
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- [사이드바 필터] ---
        st.sidebar.header("🔍 분석 필터 설정")
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 날짜", options=all_dates, default=all_dates[-2:] if len(all_dates)>1 else all_dates)
        
        all_hotels = sorted(df['호텔명'].unique())
        default_hotels = [h for h in all_hotels if "앰버" in h] + ["신라호텔", "그랜드하얏트", "파르나스", "롯데호텔"]
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔", options=all_hotels, default=[h for h in default_hotels if h in all_hotels])

        # 상세 솔팅
        st.sidebar.markdown("---")
        temp_filter = df[df['호텔명'].isin(selected_hotels)]
        selected_rooms = st.sidebar.multiselect("🛏️ 객실 타입 솔팅", options=sorted(temp_filter['객실타입'].unique()))
        selected_channels = st.sidebar.multiselect("📱 판매처 솔팅", options=sorted(df['판매처'].unique()))

        # 필터링 적용
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_rooms: f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels: f_df = f_df[f_df['판매처'].isin(selected_channels)]

        if not f_df.empty:
            # ---------------------------------------------------------
            # 1. 상단 3초 요약 카드 (Big Numbers)
            # ---------------------------------------------------------
            amber_data = f_df[f_df['호텔명'].str.contains("앰버", na=False)]
            
            st.subheader("🚀 오늘의 핵심 지표")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                if not amber_data.empty:
                    latest_price = amber_data.iloc[-1]['가격']
                    st.metric("엠버 최신 최저가", f"{latest_price:,.0f}원")
                else:
                    st.metric("엠버 최신 최저가", "데이터 없음")
            
            with m_col2:
                market_min = f_df['가격'].min()
                market_min_hotel = f_df.loc[f_df['가격'].idxmin(), '호텔명']
                st.metric("시장 전체 최저가", f"{market_min:,.0f}원", help=f"최저가 호텔: {market_min_hotel}")

            with m_col3:
                market_avg = f_df['가격'].mean()
                diff_ratio = ((latest_price - market_avg) / market_avg) * 100 if not amber_data.empty else 0
                st.metric("시장 평균가 대비", f"{diff_ratio:+.1f}%", delta_color="inverse")

            with m_col4:
                most_active_channel = f_df['판매처'].value_counts().idxmax()
                st.metric("현재 최다 노출 채널", most_active_channel)

            st.markdown("---")

            # ---------------------------------------------------------
            # 2. 신호등 가격 매트릭스 (직관적 비교)
            # ---------------------------------------------------------
            st.subheader("🚦 경쟁사 가격 매트릭스 (신호등 시스템)")
            
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            
            # 신호등 스타일 적용 함수
            def color_market_status(val):
                if pd.isna(val) or amber_data.empty: return ''
                # 각 날짜별 엠버 가격 기준
                # 여기서는 단순화를 위해 전체 날짜 중 엠버 최저가와 비교 (날짜별 비교로직 고도화 가능)
                amber_ref = amber_data['가격'].min() 
                diff = val - amber_ref
                if diff < -30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold' # 위험 (경쟁사가 훨씬 쌈)
                if diff < 0: return 'background-color: #fff3cd; color: #856404;' # 주의 (경쟁사가 약간 쌈)
                return 'background-color: #d4edda; color: #155724;' # 양호 (우리가 경쟁력 있음)

            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_market_status), 
                         use_container_width=True)
            st.caption("💡 색상 가이드: 빨강(경쟁사 위협적 저가) / 노랑(경쟁사 약우세) / 초록(엠버 가격 경쟁력 우수)")

            st.markdown("---")

            # ---------------------------------------------------------
            # 3. 객실별/채널별 정밀 분석 (히트맵 스타일)
            # ---------------------------------------------------------
            col_left, col_right = st.columns([3, 2])
            
            with col_left:
                st.subheader("💎 엠버 객실별 채널 가격 분포 (Heatmap)")
                if not amber_data.empty:
                    # 객실별/채널별 평균가 매트릭스
                    amber_pivot = amber_data.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
                    fig_heat = px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r',
                                        title="엠버 객실/채널별 최저가 분포")
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.info("엠버퓨어힐 데이터를 선택해주세요.")

            with col_right:
                st.subheader("📊 호텔별 최저가 범위")
                fig_box = px.box(f_df, x="호텔명", y="가격", color="호텔명", points="all")
                fig_box.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_box, use_container_width=True)

            # 4. 상세 로그 (최하단)
            with st.expander("📋 전체 상세 데이터 로그 보기"):
                st.dataframe(f_df.sort_values(['날짜', '수집시간'], ascending=[True, False]), use_container_width=True, hide_index=True)

        else:
            st.warning("조건에 맞는 데이터가 없습니다. 필터를 조정해주세요.")
    else:
        st.error("데이터 로드 실패. Collector.py가 정상 작동 중인지 확인하세요.")

except Exception as e:
    st.error(f"대시보드 에러: {e}")
