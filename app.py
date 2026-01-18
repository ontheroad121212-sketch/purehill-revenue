import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="엠버 AI 지배인 v6.0", layout="wide")

# 직관성을 극대화하는 맞춤형 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1a1c1e; }
    .action-card { 
        background-color: #f0f7ff; border-left: 5px solid #007bff; padding: 20px; 
        border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .parity-alert { 
        background-color: #fff5f5; border-left: 5px solid #ff4b4b; padding: 15px; 
        border-radius: 8px; margin-bottom: 10px; color: #d32f2f; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 엠버 7대 플랫폼 통합 AI 지배인 v6.0")
st.caption("AI 전략 제안 & 땡처리 추적 통합 시스템")

# 2. 데이터 불러오기 및 정밀 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=5) # 5초 실시간 갱신
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        # [데이터 정밀 정제] 매칭 오류 방지를 위해 모든 공백 제거
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        
        # 가격 숫자 변환
        data['가격'] = pd.to_numeric(data['가격'].astype(str).str.replace(',', '').str.replace('원', ''), errors='coerce')
        
        # 수집시간 및 투숙일 변환
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        data['투숙일'] = pd.to_datetime(data['날짜'], errors='coerce')
        
        # 리드타임 계산 (투숙일 - 수집일)
        data['리드타임'] = (data['투숙일'] - data['수집시간']).dt.days
        
        # 필수 데이터 누락 제거 및 150만원 상한 필터
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
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
        
        # 2. 13개 전체 호텔 리스트 고정
        target_list = ["엠버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", "조선힐스위트", "메종글래드", "그랜드조선제주"]
        all_hotels = sorted(df['호텔명'].unique())
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔 선택", options=all_hotels, default=[h for h in target_list if h in all_hotels])

        # 3. 엠버 핵심 객실 필터 고정
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 엠버 전용 핵심 객실")
        ember_core_rooms = ["그린밸리 디럭스 더블", "힐 엠버 트윈", "힐 파인 더블"]
        existing_rooms = [r for r in ember_core_rooms if r in df['객실타입'].unique()]
        selected_core_rooms = st.sidebar.multiselect("🛏️ 엠버 분석 객실 선택", options=existing_rooms, default=existing_rooms)

        # 4. 필터링 적용
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        if selected_core_rooms:
            # 엠버는 선택된 객실만, 타 호텔은 전체 유지
            f_df = f_df[ (~f_df['호텔명'].str.contains("엠버")) | (f_df['객실타입'].isin(selected_core_rooms)) ]

        # 엠버 데이터 정밀 추출
        amber_in_filter = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
        amber_min_val = amber_in_filter['가격'].min() if not amber_in_filter.empty else 0

        # ---------------------------------------------------------
        # 💡 [핵심 신규 기능 1] AI 오늘의 한 수 (Daily Action Plan)
        # ---------------------------------------------------------
        st.subheader("💡 AI 지배인 오늘의 전략 제안")
        with st.container():
            st.markdown('<div class="action-card">', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("🚩 **긴급 점검 및 조치**")
                # 파리티 경보 유무 확인
                parity_issue = False
                if not amber_in_filter.empty:
                    for (date, room), group in amber_in_filter.groupby(['날짜', '객실타입']):
                        if group['가격'].min() < group['가격'].max() - 5000: parity_issue = True
                
                if parity_issue: st.write("- 🚨 현재 일부 채널에서 **가격 역전**이 감지되었습니다. 즉시 확인하십시오.")
                else: st.write("- ✅ 모든 채널의 가격 파리티가 깨끗합니다.")

                # 땡처리 호텔 감지
                dumping_list = []
                for h in selected_hotels:
                    if "엠버" in h: continue
                    h_data = f_df[f_df['호텔명'] == h]
                    if not h_data.empty and h_data['리드타임'].min() <= 3:
                        recent_p = h_data[h_data['리드타임'] <= 3]['가격'].mean()
                        prev_p = h_data[h_data['리드타임'] > 7]['가격'].mean()
                        if recent_p < prev_p * 0.85: dumping_list.append(h)
                
                if dumping_list: st.write(f"- 🚨 **{', '.join(dumping_list)}**가 투숙 임박 땡처리를 진행 중입니다.")
                else: st.write("- 🕊️ 경쟁사들의 급격한 투매 징후는 발견되지 않았습니다.")

            with col_b:
                st.write("📈 **매출 극대화 제안**")
                if amber_min_val > 0:
                    comp_min = f_df[~f_df['호텔명'].str.contains("엠버")]['가격'].min() if not f_df[~f_df['호텔명'].str.contains("엠버")].empty else 0
                    if amber_min_val > comp_min + 50000: st.write("- 📉 시장 대비 엠버가 고가입니다. 소폭 인하로 예약 선점이 필요합니다.")
                    elif amber_min_val < comp_min - 30000: st.write("- 💰 엠버가 압도적 저가입니다! 만 원 정도 인상하여 수익률을 높이십시오.")
                    else: st.write("- ✨ 현재 적정 시장가를 유지 중입니다. 현 상태를 유지하십시오.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 🟢 실시간 가격 역전 탐지 (Parity Check)
        # ---------------------------------------------------------
        st.subheader("⚠️ 실시간 가격 역전 상세 알림")
        if not amber_in_filter.empty:
            parity_alerts = []
            for (date, room), group in amber_in_filter.groupby(['날짜', '객실타입']):
                official_price = group['가격'].max()
                broken_channels = group[group['가격'] < official_price]
                for _, row in broken_channels.iterrows():
                    gap = official_price - row['가격']
                    if gap > 5000:
                        parity_alerts.append(f"🚨 **[가격 무너짐]** {row['날짜']} | {row['객실타입']} | **{row['판매처']}** 가 기준보다 **{gap:,.0f}원** 낮음!")
            
            if parity_alerts:
                for alert in parity_alerts[:5]: st.markdown(f'<div class="parity-alert">{alert}</div>', unsafe_allow_html=True)
            else: st.success("✅ 가격 파리티 정상")

        # ---------------------------------------------------------
        # 📉 [핵심 신규 기능 2] 경쟁사 땡처리 추적 (Booking Pace)
        # ---------------------------------------------------------
        st.subheader("📉 투숙 임박 땡처리 추적 (Lead-time Analysis)")
        pace_trend = f_df.groupby(['리드타임', '호텔명'])['가격'].min().reset_index()
        fig_pace = px.line(pace_trend, x='리드타임', y='가격', color='호텔명', markers=True, title="리드타임별 최저가 추이 (오른쪽이 투숙일 임박)")
        fig_pace.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_pace, use_container_width=True)

        st.markdown("---")

        # 1. 지표 요약
        st.subheader("🚀 실시간 시장 요약")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("엠버 최저가", f"{amber_min_val:,.0f}원" if amber_min_val > 0 else "데이터 없음")
        m2.metric("시장 전체 최저가", f"{f_df['가격'].min():,.0f}원" if not f_df.empty else "0원")
        m3.metric("시장 평균가", f"{f_df['가격'].mean():,.0f}원" if not f_df.empty else "0원")
        m4.metric("활성 1위 채널", f_df['판매처'].value_counts().idxmax() if not f_df.empty else "없음")

        # 2. 신호등 매트릭스
        st.subheader("🚦 일자별 호텔 최저가 매트릭스")
        if not f_df.empty:
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            def color_signal(val):
                if pd.isna(val) or amber_min_val == 0: return ''
                if val < amber_min_val - 30000: return 'background-color: #ffcccc; color: #d32f2f;'
                if val < amber_min_val: return 'background-color: #fff3cd;'
                return 'background-color: #d4edda;'
            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_signal), use_container_width=True)

        # 3. 엠버 핵심 객실 히트맵
        st.subheader("💎 엠버 핵심 객실별/채널별 최저가 분포 (Heatmap)")
        if not amber_in_filter.empty:
            amber_pivot = amber_in_filter.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
            st.plotly_chart(px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto"), use_container_width=True)

        # 4. 날짜별 전수 추적 그래프
        st.subheader("📊 날짜별 전수 추적 그래프")
        for date in selected_dates:
            d_df = f_df[f_df['날짜'] == date].sort_values('수집시간')
            if not d_df.empty:
                st.plotly_chart(px.line(d_df, x='수집시간', y='가격', color='호텔명', markers=True, title=f"📅 {date} 투숙일 실시간 가격 추이"), use_container_width=True)

        # 5. 가격 조정 시뮬레이터
        st.markdown("---")
        st.subheader("🎯 엠버 가격 조정 시뮬레이터")
        if amber_min_val > 0:
            s1, s2 = st.columns([1, 2])
            with s1:
                delta = st.slider("가격을 조정해보세요 (원)", -150000, 150000, 0, 5000)
                sim_p = amber_min_val + delta
                st.write(f"📈 **조정 후 예상가: {sim_p:,.0f}원**")
            comp_p = f_df[~f_df['호텔명'].str.contains("엠버")]['가격'].values
            if len(comp_p) > 0:
                comb = np.append(comp_p, sim_p); comb.sort()
                rank = np.where(comb == sim_p)[0][0] + 1
                st.write(f"🏆 예상 시장 순위: **{len(comb)}개 중 {rank}위**")
                st.progress((len(comb) - rank + 1) / len(comb))

        with st.expander("📋 상세 로그 보기"):
            st.dataframe(f_df.sort_values(['날짜', '수집시간'], ascending=[True, False]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"대시보드 에러 발생: {e}")
