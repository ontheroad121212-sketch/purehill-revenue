import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="엠버 AI 지배인 v6.2", layout="wide")

# 디자인 수정: 남색 바(gm-card) 내부의 가독성 향상
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .gm-card { 
        background-color: #1b263b; color: white; padding: 25px; 
        border-radius: 15px; margin-bottom: 25px; border-left: 10px solid #e0e1dd;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .gm-card h3 { color: #e0e1dd !important; margin-bottom: 20px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e9ecef; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
    .action-card { background-color: #f0f7ff; border-left: 5px solid #007bff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .parity-alert { background-color: #fff5f5; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 8px; margin-bottom: 10px; color: #d32f2f; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 엠버 7대 플랫폼 통합 AI 지배인 v7.2")
st.caption("매트릭스 상세 분석 및 KPI 리포트 시스템")

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
        data['판매처'] = data['판매처'].astype(str).str.strip()
        data['가격'] = pd.to_numeric(data['가격'].astype(str).str.replace(',', '').str.replace('원', ''), errors='coerce')
        
        # 날짜 데이터 처리 (그래프 핵심 컬럼)
        data['수집시간_dt'] = pd.to_datetime(data['수집시간'], errors='coerce')
        # '수집일' 컬럼 강제 생성 (YYYY-MM-DD 형식)
        data['수집일'] = data['수집시간_dt'].dt.date 
        data['투숙일_dt'] = pd.to_datetime(data['날짜'], errors='coerce')
        
        data = data.dropna(subset=['호텔명', '가격', '날짜', '수집일'])
        
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

        # 3. [업데이트] 판매처(채널) 필터 - 지배인님 요청 채널 전수 반영
        st.sidebar.markdown("---")
        st.sidebar.header("📱 판매처(채널) 필터")
        # 수집 데이터에 있는 실제 채널 리스트 추출
        all_channels = sorted(df['판매처'].unique())
        selected_channels = st.sidebar.multiselect("모니터링 채널 선택", options=all_channels, default=all_channels)

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
        # 필터링 로직 (오류 해결을 위해 상단으로 이동)
        # ---------------------------------------------------------
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels)) & (df['판매처'].isin(selected_channels))]
    
        # 엠버와 경쟁사 데이터 분리 (AI 리포트에서 사용됨)
        amber_df = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
        comp_df = f_df[~f_df['호텔명'].str.contains("엠버", na=False)]
 
        # ---------------------------------------------------------
        # 🤖 AI 자동 경영 분석 리포트 모듈 (수정 완료)
        # ---------------------------------------------------------
        st.markdown('<div class="ai-report-card">', unsafe_allow_html=True)
        st.subheader("🤖 AI Executive Intelligence Report")
    
        if not amber_df.empty and not comp_df.empty:
            amber_avg = amber_df['가격'].mean()
            market_avg = comp_df['가격'].mean()
            mpi = (amber_avg / market_avg) * 100
            status = "우수" if mpi > 110 else "안정" if mpi > 95 else "주의"
        
            st.markdown(f"""
            **[엠버퓨어힐 수익성 분석 결론]**
            현재 엠버의 시장 지배력 지수(MPI)는 **{mpi:.1f}%**로 시장 평균 대비 **{status}**한 상태입니다. 
        
            1. **경쟁사 동향:** 최근 수집된 데이터 기준 경쟁사들의 최저가는 {comp_df['가격'].min():,.0f}원입니다.
            2. **가격 파리티:** 선택된 채널 중 기준가와 차이가 발생하는 플랫폼이 있는지 하단 상세 알림을 확인하십시오.
            3. **수익 전략:** 현재 엠버의 포지셔닝은 시장가 대비 프리미엄을 유지하고 있습니다.
            """)
        else:
            st.info("💡 사이드바에서 엠버와 경쟁 호텔을 선택하시면 AI 분석이 시작됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ---------------------------------------------------------
        # 👑 [수정 완료] 총지배인용 KPI 경영 요약 섹션
        # ---------------------------------------------------------
        # 에러 수정 포인트: .contains() -> .str.contains()
        amber_df = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
        comp_df = f_df[~f_df['호텔명'].str.contains("엠버", na=False)]
        
        st.markdown('<div class="gm-card">', unsafe_allow_html=True)
        st.subheader("🏁 Executive Summary (경영 지표 요약)")
        
        if not amber_df.empty and not comp_df.empty:
            kpi1, kpi2, kpi3 = st.columns(3)
            
            # 1. MPI (Market Penetration Index)
            amber_avg = amber_df['가격'].mean()
            market_avg = comp_df['가격'].mean()
            mpi = (amber_avg / market_avg) * 100
            kpi1.metric("시장 지배력 지수(MPI)", f"{mpi:.1f}%", f"{mpi-100:+.1f}% vs 시장평균")
            
            # 2. 가격 안정성 점수
            price_std = amber_df['가격'].std()
            stability = 100 - (price_std / amber_avg * 100) if amber_avg > 0 else 0
            kpi2.metric("가격 방어 안정성", f"{max(0, stability):.1f}점", "채널별 균등가 유지")
            
            # 3. 투숙 임박 수익 기회 (경쟁사 땡처리 대비 엠버의 프리미엄폭)
            comp_min = comp_df['가격'].min()
            kpi3.metric("프리미엄 수익폭", f"{amber_avg - comp_min:,.0f}원", "경쟁사 최저가 대비")
        else:
            # 데이터가 없을 때 남색 바가 텅 비지 않도록 안내 문구 추가
            st.info("💡 사이드바에서 '엠버퓨어힐'과 '비교 호텔'을 모두 선택하시면 경영 지표가 산출됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)
    
        # ---------------------------------------------------------
        # 💡 [핵심 기능 1] AI 오늘의 한 수 (Daily Action Plan)
        # ---------------------------------------------------------
        st.subheader("💡 AI 지배인 오늘의 전략 제안")
        with st.container():
            st.markdown('<div class="action-card">', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("🚩 **긴급 점검 및 조치**")
                parity_issue = False
                if not amber_in_filter.empty:
                    for (date, room), group in amber_in_filter.groupby(['날짜', '객실타입']):
                        if group['가격'].min() < group['가격'].max() - 5000: parity_issue = True
                
                if parity_issue: st.write("- 🚨 현재 일부 채널에서 **가격 역전**이 감지되었습니다. 즉시 확인하십시오.")
                else: st.write("- ✅ 모든 채널의 가격 파리티가 깨끗합니다.")

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

        # 🟢 실시간 가격 역전 상세 알림
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

        # 📉 [핵심 기능 2] 경쟁사 땡처리 추적 (Booking Pace)
        st.subheader("📉 투숙 임박 땡처리 추적 (Lead-time Analysis)")
        pace_trend = f_df.groupby(['리드타임', '호텔명'])['가격'].min().reset_index()
        fig_pace = px.line(pace_trend, x='리드타임', y='가격', color='호텔명', markers=True, title="리드타임별 최저가 추이 (오른쪽이 투숙일 임박)")
        fig_pace.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_pace, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # 🚦 [지배인님 요청] 일자별 호텔 상세 최저가 매트릭스
        # ---------------------------------------------------------
        st.subheader("🚦 일자별 호텔 상세 최저가 매트릭스 (판매처/객실 포함)")
        
        def get_min_detail(x):
            if x.empty: return "-"
            min_row = x.loc[x['가격'].idxmin()]
            return f"{min_row['가격']:,.0f}원\n({min_row['판매처']} / {min_row['객실타입']})"

        detail_pivot = f_df.groupby(['호텔명', '날짜']).apply(get_min_detail).unstack()

        def color_signal(val):
            if val == "-" or amber_min_val == 0: return ''
            try:
                price_val = int(val.split('원')[0].replace(',', ''))
                if price_val < amber_min_val - 30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold;'
                if price_val < amber_min_val: return 'background-color: #fff3cd;'
                return 'background-color: #d4edda;'
            except: return ''

        st.dataframe(detail_pivot.style.applymap(color_signal), use_container_width=True)
        st.caption("※ 표기 형식: 최저가 (판매처 / 객실타입)")

        st.markdown("---")

        # 1. 지표 요약
        st.subheader("🚀 실시간 시장 요약")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("엠버 최저가", f"{amber_min_val:,.0f}원" if amber_min_val > 0 else "데이터 없음")
        m2.metric("시장 전체 최저가", f"{f_df['가격'].min():,.0f}원" if not f_df.empty else "0원")
        m3.metric("시장 평균가", f"{f_df['가격'].mean():,.0f}원" if not f_df.empty else "0원")
        m4.metric("활성 1위 채널", f_df['판매처'].value_counts().idxmax() if not f_df.empty else "없음")

        # 2. 엠버 핵심 객실 히트맵
        st.subheader("💎 엠버 핵심 객실별/채널별 최저가 분포 (Heatmap)")
        if not amber_in_filter.empty:
            amber_pivot = amber_in_filter.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
            st.plotly_chart(px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto"), use_container_width=True)

        # 3. 날짜별 전수 추적 그래프
        st.subheader("📊 수집일 기준 가격 변동 추이 (일자별)")
        for date in selected_dates:
            d_df = f_df[f_df['날짜'] == date].copy()
            if not d_df.empty:
                # 같은 날 수집된 데이터는 최저가로 그룹화하여 일자별 추이 생성
                daily_trend = d_df.groupby(['수집일', '호텔명'])['가격'].min().reset_index()
                fig = px.line(daily_trend, x='수집일', y='가격', color='호텔명', markers=True, 
                             title=f"📅 {date} 투숙일의 수집일별 가격 흐름")
                fig.update_layout(xaxis_title="데이터 수집일", yaxis_title="최저가 (원)")
                st.plotly_chart(fig, use_container_width=True)
                
        # 4. 시뮬레이터
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
