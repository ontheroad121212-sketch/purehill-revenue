import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 전략 대시보드", layout="wide")

# 직관성을 극대화하는 맞춤형 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1a1c1e; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 12px; }
    .parity-alert { 
        background-color: #fff5f5; 
        border-left: 5px solid #ff4b4b; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 10px; 
        color: #d32f2f; 
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인 v5.0")
st.caption("가격 역전 실시간 탐지 및 시장 점유율 공략 시스템")

# 2. 데이터 불러오기 및 정밀 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 10초 실시간 갱신
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        # 데이터 정밀 정제
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        # [지배인님 요청] 150만원 상한 필터
        data = data[data['가격'] < 1500000]
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # ---------------------------------------------------------
        # 🟢 [기능 1] 가격 역전 알림 (Parity Alert) - 최상단 배치
        # ---------------------------------------------------------
        st.subheader("⚠️ 실시간 가격 역전 탐지 (Parity Check)")
        amber_all = df[df['호텔명'].str.contains("앰버", na=False)]
        
        if not amber_all.empty:
            parity_alerts = []
            # 날짜와 객실별로 그룹화하여 채널 간 가격 차이 확인
            for (date, room), group in amber_all.groupby(['날짜', '객실타입']):
                # 지배인이 설정한 기준가 (해당 그룹 내 최고가로 가정)
                official_price = group['가격'].max() 
                # 기준가보다 낮게 파는 채널 탐지
                broken_channels = group[group['가격'] < official_price]
                
                for _, row in broken_channels.iterrows():
                    gap = official_price - row['가격']
                    if gap > 5000: # 5천원 이상 벌어지면 경고
                        parity_alerts.append(f"🚨 **[가격 무너짐]** {row['날짜']} | {row['객실타입']} | **{row['판매처']}** 판매가가 기준보다 **{gap:,.0f}원** 낮습니다!")

            if parity_alerts:
                for alert in parity_alerts[:5]: # 너무 많으면 5개만 노출
                    st.markdown(f'<div class="parity-alert">{alert}</div>', unsafe_allow_html=True)
            else:
                st.success("✅ 모든 채널의 가격이 통제 범위 내에 있습니다.")

        # --- [사이드바 필터 구역] ---
        st.sidebar.header("🔍 분석 필터 설정")
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 투숙일", options=all_dates, default=all_dates if all_dates else [])
        
        target_list = ["앰버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", "조선힐스위트", "메종글래드", "그랜드조선제주"]
        all_hotels = sorted(df['호텔명'].unique())
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔", options=all_hotels, default=[h for h in target_list if h in all_hotels])

        st.sidebar.markdown("---")
        temp_f = df[df['호텔명'].isin(selected_hotels)]
        selected_rooms = st.sidebar.multiselect("🛏️ 객실 타입 솔팅", options=sorted(temp_f['객실타입'].unique()))
        selected_channels = st.sidebar.multiselect("📱 판매처 솔팅", options=sorted(df['판매처'].unique()))

        # 데이터 필터링 적용
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_rooms: f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels: f_df = f_df[f_df['판매처'].isin(selected_channels)]

        if not f_df.empty:
            # ---------------------------------------------------------
            # 1. 상단 핵심 지표
            # ---------------------------------------------------------
            st.subheader("🚀 실시간 시장 지위 요약")
            amber_data = f_df[f_df['호텔명'].str.contains("앰버", na=False)]
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                if not amber_data.empty:
                    amber_min_val = amber_data['가격'].min()
                    st.metric("앰버 최저가", f"{amber_min_val:,.0f}원")
                else: st.metric("앰버 최저가", "데이터 없음")
            with m_col2:
                market_min = f_df['가격'].min()
                st.metric("시장 전체 최저가", f"{market_min:,.0f}원")
            with m_col3:
                market_avg = f_df['가격'].mean()
                if not amber_data.empty:
                    diff = ((amber_min_val - market_avg) / market_avg) * 100
                    st.metric("시장 평균가 대비", f"{diff:+.1f}%", delta_color="inverse")
                else: st.metric("시장 평균가 대비", "-")
            with m_col4:
                st.metric("활성 1위 채널", f_df['판매처'].value_counts().idxmax())

            st.markdown("---")

            # ---------------------------------------------------------
            # 2. 신호등 매트릭스
            # ---------------------------------------------------------
            st.subheader("🚦 일자별 호텔 최저가 매트릭스 (신호등)")
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            def color_signal(val):
                if pd.isna(val) or amber_data.empty: return ''
                ref = amber_data['가격'].min()
                if val < ref - 30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold'
                if val < ref: return 'background-color: #fff3cd; color: #856404;'
                return 'background-color: #d4edda; color: #155724;'
            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_signal), use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 3. 앰버 정밀 분석 (히트맵)
            # ---------------------------------------------------------
            st.subheader("💎 앰버 객실별/채널별 최저가 분포")
            if not amber_data.empty:
                amber_pivot = amber_data.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
                st.plotly_chart(px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto"), use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 4. 날짜별 개별 트렌드 (무삭제 전수 노출)
            # ---------------------------------------------------------
            st.subheader("📉 날짜별 가격 변동 개별 트렌드")
            for date in selected_dates:
                date_df = f_df[f_df['날짜'] == date].sort_values('수집시간')
                if not date_df.empty:
                    fig = px.line(date_df, x='수집시간', y='가격', color='호텔명', markers=True, title=f"📅 {date} 투숙일 가격 추이")
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 🔵 [기능 2] 시장 점유율 시뮬레이션 (Simulator)
            # ---------------------------------------------------------
            st.subheader("🎯 앰버 가격 조정 시뮬레이터 (Market Share Strategy)")
            if not amber_data.empty:
                sim_col1, sim_col2 = st.columns([1, 2])
                with sim_col1:
                    st.write("🔧 **가격 조정**")
                    delta = st.slider("가격을 얼마나 조정해볼까요?", -150000, 150000, 0, 5000)
                    sim_price = amber_min_val + delta
                    st.write(f"📈 **조정 후 앰버가: {sim_price:,.0f}원**")
                
                with sim_col2:
                    # 경쟁사 최저가 리스트 추출
                    comp_prices = f_df[~f_df['호텔명'].str.contains("앰버")].groupby('호텔명')['가격'].min().values
                    combined = np.append(comp_prices, sim_price)
                    combined.sort()
                    rank = np.where(combined == sim_price)[0][0] + 1
                    total = len(combined)
                    score = ((total - rank + 1) / total) * 100
                    
                    st.write(f"🏆 **예상 시장 순위:** {total}개 호텔 중 **{rank}위**")
                    st.progress(score / 100)
                    st.write(f"📍 **가격 경쟁력 점수:** {score:.1f}점")
                    if rank == 1: st.success("🥇 현재 시장 최저가입니다! 점유율 독점이 예상됩니다.")
                    elif rank <= 3: st.info("🥈 시장 상위권 가격입니다. 안정적인 예약 유입이 가능합니다.")
                    else: st.warning("🥉 경쟁 호텔 대비 가격이 높습니다. 추가 조정이 필요할 수 있습니다.")

            st.markdown("---")
            with st.expander("📋 전체 데이터 로그"):
                st.dataframe(f_df.sort_values(['날짜', '수집시간'], ascending=[True, False]), use_container_width=True, hide_index=True)

        else: st.warning("필터 조건에 맞는 데이터가 없습니다.")
    else: st.warning("데이터 로드 실패.")
except Exception as e:
    st.error(f"오류 발생: {e}")
