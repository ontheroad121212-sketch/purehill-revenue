import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 설정 및 디자인 (전체 레이아웃)
st.set_page_config(page_title="앰버 AI 지배인 전략 대시보드", layout="wide")

# 직관성을 극대화하는 맞춤형 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1a1c1e; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 12px; }
    .parity-alert { 
        background-color: #fff5f5; border-left: 5px solid #ff4b4b; padding: 15px; 
        border-radius: 8px; margin-bottom: 10px; color: #d32f2f; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인 v5.2")
st.caption("전수 데이터 모니터링 및 실시간 가격 역전 탐지 시스템 (v5.2)")

# 2. 데이터 불러오기 및 정밀 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 10초마다 실시간 갱신
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제]
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        
        # 가격: 콤마와 '원' 제거 후 숫자로 변환
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        
        # 수집시간: 날짜 형식으로 변환
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        # 필수 데이터 누락 행 제거
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        
        # [지배인님 요청] 150만원 이상 고가 객실 제외
        data = data[data['가격'] < 1500000]
        
        return data
    except Exception as e:
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- [사이드바 필터 구역] ---
        st.sidebar.header("🔍 분석 필터 설정")
        
        # 1. 날짜 멀티 선택
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 투숙일 선택", options=all_dates, default=[all_dates[-1]] if all_dates else [])
        
        # 2. 13개 전체 호텔 리스트 (지배인님 고정 리스트)
        target_list = [
            "앰버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", 
            "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", 
            "조선힐스위트", "메종글래드", "그랜드조선제주"
        ]
        all_hotels = sorted(df['호텔명'].unique())
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔 선택", options=all_hotels, default=[h for h in target_list if h in all_hotels])

        # 3. 상세 솔팅 (객실 및 채널)
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 정밀 솔팅 (객실/채널)")
        temp_filter_data = df[df['호텔명'].isin(selected_hotels)]
        selected_rooms = st.sidebar.multiselect("🛏️ 특정 객실 타입만 보기", options=sorted(temp_filter_data['객실타입'].unique()))
        selected_channels = st.sidebar.multiselect("📱 특정 판매처만 보기", options=sorted(df['판매처'].unique()))

        # 데이터 필터링 적용
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_rooms: f_df = f_df[f_df['객실타입'].isin(selected_rooms)]
        if selected_channels: f_df = f_df[f_df['판매처'].isin(selected_channels)]

        # ---------------------------------------------------------
        # 🟢 [기능 1] 가격 역전 알림 (Parity Alert) - 에러 방지 포함
        # ---------------------------------------------------------
        st.subheader("⚠️ 실시간 가격 역전 탐지 (Parity Check)")
        amber_in_filter = f_df[f_df['호텔명'].str.contains("앰버", na=False)]
        
        if not amber_in_filter.empty:
            parity_alerts = []
            for (date, room), group in amber_in_filter.groupby(['날짜', '객실타입']):
                official_price = group['가격'].max()
                broken_channels = group[group['가격'] < official_price]
                for _, row in broken_channels.iterrows():
                    gap = official_price - row['가격']
                    if gap > 5000:
                        parity_alerts.append(f"🚨 **[가격 무너짐]** {row['날짜']} | {row['객실타입']} | **{row['판매처']}** 가격이 기준보다 **{gap:,.0f}원** 낮음!")
            
            if parity_alerts:
                for alert in parity_alerts[:5]:
                    st.markdown(f'<div class="parity-alert">{alert}</div>', unsafe_allow_html=True)
            else:
                st.success("✅ 선택된 조건 내 가격 파리티가 정상입니다.")
        else:
            st.info("💡 사이드바에서 '앰버퓨어힐'을 포함하여 날짜를 선택해 주세요.")

        if not f_df.empty:
            st.markdown("---")
            # ---------------------------------------------------------
            # 1. 상단 핵심 지표 요약
            # ---------------------------------------------------------
            st.subheader("🚀 실시간 시장 지위 요약")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            amber_min_val = 0
            if not amber_in_filter.empty:
                amber_min_val = amber_in_filter['가격'].min()
                with m_col1:
                    st.metric("앰버 최저가", f"{amber_min_val:,.0f}원")
            else:
                with m_col1:
                    st.metric("앰버 최저가", "데이터 없음")
            
            with m_col2:
                market_min_val = f_df['가격'].min()
                st.metric("시장 전체 최저가", f"{market_min_val:,.0f}원")
                
            with m_col3:
                if not amber_in_filter.empty:
                    market_avg = f_df['가격'].mean()
                    diff = ((amber_min_val - market_avg) / market_avg) * 100
                    st.metric("시장 평균가 대비", f"{diff:+.1f}%", delta_color="inverse")
                else:
                    st.metric("시장 평균가 대비", "-")
            
            with m_col4:
                top_chan = f_df['판매처'].value_counts().idxmax()
                st.metric("활성 1위 채널", top_chan)

            st.markdown("---")

            # ---------------------------------------------------------
            # 2. 신호등 가격 매트릭스
            # ---------------------------------------------------------
            st.subheader("🚦 일자별 호텔 최저가 매트릭스 (신호등)")
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            def color_signal(val):
                if pd.isna(val) or amber_in_filter.empty: return ''
                ref = amber_in_filter['가격'].min()
                if val < ref - 30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold'
                if val < ref: return 'background-color: #fff3cd; color: #856404;'
                return 'background-color: #d4edda; color: #155724;'
            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_signal), use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 3. 앰버 정밀 분석 (히트맵)
            # ---------------------------------------------------------
            st.subheader("💎 엠버 객실별/채널별 최저가 분포 (Heatmap)")
            if not amber_in_filter.empty:
                amber_pivot = amber_in_filter.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
                fig_heat = px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto")
                st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 4. 날짜별 개별 트렌드 (생략 없이 전수 노출)
            # ---------------------------------------------------------
            st.subheader("📉 날짜별 가격 변동 개별 트렌드 (Pickup Analysis)")
            for date in selected_dates:
                date_spec_df = f_df[f_df['날짜'] == date].sort_values('수집시간')
                if not date_spec_df.empty:
                    fig = px.line(date_spec_df, x='수집시간', y='가격', color='호텔명', markers=True, title=f"📅 {date} 투숙일 가격 추이")
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # ---------------------------------------------------------
            # 🔵 [기능 2] 시장 점유율 시뮬레이션 (Simulator)
            # ---------------------------------------------------------
            st.subheader("🎯 앰버 가격 조정 시뮬레이터")
            if not amber_in_filter.empty:
                sim_col1, sim_col2 = st.columns([1, 2])
                with sim_col1:
                    delta = st.slider("가격을 조정해보세요 (원)", -150000, 150000, 0, 5000)
                    sim_price = amber_min_val + delta
                    st.write(f"📈 **조정 후 예상가: {sim_price:,.0f}원**")
                with sim_col2:
                    comp_prices = f_df[~f_df['호텔명'].str.contains("앰버")].groupby('호텔명')['가격'].min().values
                    if len(comp_prices) > 0:
                        combined = np.append(comp_prices, sim_price)
                        combined.sort()
                        rank = np.where(combined == sim_price)[0][0] + 1
                        total = len(combined)
                        score = ((total - rank + 1) / total) * 100
                        st.write(f"🏆 **예상 시장 순위:** {total}개 중 **{rank}위**")
                        st.progress(score / 100)
                    else:
                        st.write("비교할 경쟁사 데이터가 부족합니다.")

            st.markdown("---")
            # ---------------------------------------------------------
            # 5. 상세 데이터 로그 및 박스플롯
            # ---------------------------------------------------------
            col_low_a, col_low_b = st.columns([2, 1])
            with col_low_a:
                st.subheader("📋 전체 상세 데이터 로그")
                st.dataframe(f_df.sort_values(['날짜', '가격'], ascending=[True, True]), use_container_width=True, hide_index=True)
            with col_low_b:
                st.subheader("📊 호텔별 가격 분포 범위")
                fig_box = px.box(f_df, x="호텔명", y="가격", color="호텔명")
                fig_box.update_layout(showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)

        else:
            st.warning("선택된 필터 조건에 데이터가 없습니다.")
    else:
        st.warning("데이터 로드 중입니다. 시트 확인 및 수집기를 실행해 주세요.")

except Exception as e:
    st.error(f"대시보드 에러: {e}")
