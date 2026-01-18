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
    .main { background-color: #f4f7f6; }
    
    /* 1. 표 전체 간격 압축 (Padding 최소화) */
    .dataframe td, .dataframe th {
        padding: 2px 4px !important;  /* 기존 여백을 2px로 극단적 축소 */
        line-height: 1.1 !important;
        border: 1px solid #eee !important;
    }
    
    /* 2. 표 제목(인덱스) 크기 및 볼드체 축소 */
    th.col_heading, th.row_heading {
        font-size: 10px !important;
        font-weight: 600 !important;
        background-color: #f8f9fa !important;
    }

    /* 3. 본문 가격 텍스트 (2포인트 축소 및 간격 제거) */
    .price-font {
        font-size: 11px !important; 
        font-weight: 700;
        display: block;
        margin-bottom: -2px; /* 아래 글자와의 간격 강제 축소 */
    }

    /* 4. 판매처/객실명 초소형 텍스트 */
    .small-font {
        font-size: 8.5px !important; 
        color: #888 !important;
        line-height: 1.0 !important;
        display: block;
    }

    /* 5. 기타 경영 카드 스타일 유지 */
    .gm-card { background-color: #1b263b; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e9ecef; }
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
        # [수정 포인트] 수집일을 문자열로 변환하여 에러 방지
        data['수집일'] = data['수집시간_dt'].dt.strftime('%Y-%m-%d')
        data['투숙일_dt'] = pd.to_datetime(data['날짜'], errors='coerce')
        
        data = data.dropna(subset=['호텔명', '가격', '날짜', '수집일'])
        
        # 리드타임 계산 (투숙일 - 수집일)
        # datetime 객체끼리 계산하기 위해 수집시간_dt 사용
        data['리드타임'] = (pd.to_datetime(data['날짜']) - data['수집시간_dt']).dt.days
        
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
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 투숙일 선택", options=all_dates, default=[all_dates[-1]] if all_dates else [])
        
        target_list = ["엠버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", "조선힐스위트", "메종글래드", "그랜드조선제주"]
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔 선택", options=sorted(df['호텔명'].unique()), default=[h for h in target_list if h in df['호텔명'].unique()])
        
        all_channels = sorted(df['판매처'].unique())
        selected_channels = st.sidebar.multiselect("📱 판매처(채널) 필터", options=all_channels, default=all_channels)

        ember_core_rooms = ["그린밸리", "힐 엠버", "힐 파인"] # 필터링 확률을 높이기 위해 단어를 짧게 수정
        selected_core_rooms = st.sidebar.multiselect("🎯 엠버 분석 객실 키워드", options=ember_core_rooms, default=ember_core_rooms)

        # 1차 필터링
        f_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels)) & (df['판매처'].isin(selected_channels))]
        
        # [핵심] 20만원대 누락 방지: 엠버 객실명 '포함' 방식 필터링
        if selected_core_rooms:
            ember_mask = f_df['호텔명'].str.contains("엠버", na=False)
            # 엠버가 아닌 호텔은 유지, 엠버는 키워드 포함된 것만 유지
            f_df = f_df[ (~ember_mask) | 
                         (f_df['객실타입'].str.contains('|'.join(selected_core_rooms), na=False)) ]

        # 데이터 분리 및 최저가 재산출
        amber_df = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
        comp_df = f_df[~f_df['호텔명'].str.contains("엠버", na=False)]
        amber_min_val = amber_df['가격'].min() if not amber_df.empty else 0

        # 엠버와 경쟁사 데이터 분리 (AI 리포트에서 사용됨)
        amber_df = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
        comp_df = f_df[~f_df['호텔명'].str.contains("엠버", na=False)]
        
        # 엠버 데이터 정밀 추출용 가격 변수
        amber_min_val = amber_df['가격'].min() if not amber_df.empty else 0
        amber_in_filter = amber_df # 호환성을 위해 유지

        # ---------------------------------------------------------
        # 🤖 AI 자동 경영 분석 리포트 모듈 (수정 완료)
        # ---------------------------------------------------------
        st.markdown('<div class="ai-report-card">', unsafe_allow_html=True)
        st.subheader("📊 AI 수익 경영 정밀 리포트")

        if not amber_df.empty and not comp_df.empty:
            # 1. 상세 지표 계산
            amber_avg = amber_df['가격'].mean()
            comp_min = comp_df['가격'].min()
            market_avg = comp_df['가격'].mean()
            mpi = (amber_avg / market_avg) * 100
    
            # 2. 상황별 맞춤 메시지 생성 (프롬프트 핵심)
            if mpi < 75:
                strategy = "🔥 공격적 점유율 확대 구간 (Aggressive Growth)"
                action = f"경쟁사 최저가({comp_min:,.0f}원) 대비 현재 엠버는 매우 강력한 가격 우위에 있습니다. 점유율 65% 달성 전까지는 현재가 유지가 유리하나, 주말(토) 요금은 즉시 {amber_avg*1.15:,.0f}원으로 상향 조정을 제안합니다."
            elif 75 <= mpi < 95:
                strategy = "⚖️ 수익성-점유율 균형 구간 (Balanced Yield)"
                action = "핵심 채널(아고다/트립닷컴)의 요금을 실시간 모니터링하여 MPI를 90%선까지 야금야금 끌어올리며 마진을 확보해야 합니다."
            else:
                strategy = "💎 프리미엄 수익 극대화 구간 (Premium Value)"
                action = "시장 평균보다 고가입니다. 객실 가동률이 50% 미만으로 떨어지지 않도록 투숙 3일 전 땡처리 물량을 전략적으로 배분하십시오."

            # --- [여기서부터 복사해서 붙여넣으세요] ---
            
            st.markdown("---") # 구분선 하나 넣어주면 깔끔합니다.
            major_channels = ['아고다', '트립닷컴']
            # 엠버의 아고다/트립닷컴 데이터만 추출
            amber_major_df = amber_df[amber_df['판매처'].isin(major_channels)]
            
            if not amber_major_df.empty:
                major_avg = amber_major_df['가격'].mean()
                # 시장 평균 대비 엠버의 글로벌 채널 가격 지수
                price_gap = (major_avg / market_avg) * 100
                
                st.write(f"🌐 **글로벌 주요 채널 분석 (아고다/트립닷컴)**")
                col1, col2 = st.columns(2)
                col1.write(f"• 엠버 글로벌 평균: **{major_avg:,.0f}원**")
                col2.write(f"• 글로벌 가격 지수: **{price_gap:.1f}%**")
                
                if price_gap < 85:
                    st.warning("⚠️ **글로벌 채널 저가 경보:** 시장가 대비 너무 낮습니다. 인바운드 점유율 폭발 가능성이 있으나 단가 방어가 필요합니다.")
                elif price_gap > 110:
                    st.error("🚨 **글로벌 채널 고가 경보:** 아고다/트립닷컴 가격이 너무 높아 해외 예약 유입이 차단될 수 있습니다.")
                else:
                    st.success("✅ **글로벌 채널 안정:** 아고다와 트립닷컴 요금이 시장 흐름에 맞춰 적절히 세팅되어 있습니다.")
            
            # --- [여기까지] ---

            # 기존 수익성 분석 결론 텍스트...
            st.markdown(f"""
            **[엠버퓨어힐 수익성 분석 결론]**
            현재 엠버의 전체 MPI는 **{mpi:.1f}%**입니다. 점유율 50%대에서 70%로 가기 위한... (기존 내용)
            """)

            st.markdown(f"""
            **[오늘의 경영 전략]: {strategy}**
    
            * **시장 지배력(MPI):** {mpi:.1f}% (시장 평균 {market_avg:,.0f}원 대비 {amber_avg:,.0f}원)
            * **수익 분석:** 현재 점유율 50%대에서 매출 170억 목표 달성을 위해서는 객실 단가(ADR) 보다는 **가동률(Occ) 70% 선점**이 최우선 과제입니다.
            * **실행 지침:** {action}
            """)
    
    
    
        else:
            st.info("💡 분석을 위한 충분한 데이터가 확보되지 않았습니다. 필터를 조정해 주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ---------------------------------------------------------
        # 👑 [수정 완료] 총지배인용 KPI 경영 요약 섹션
        # ---------------------------------------------------------
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
                    comp_min = comp_df['가격'].min() if not comp_df.empty else 0
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

        # 🚦 일자별 호텔 상세 최저가 매트릭스 (인덱스 복구 및 열 너비 고정형)
        st.subheader("🚦 일자별 호텔 상세 최저가 매트릭스 (판매처/객실 포함)")
        
        def get_min_detail(x):
            if x.empty: return "-"
            # 무조건 가격이 가장 낮은 행을 첫 번째로 가져옴 (20만원대 요금 확보)
            min_row = x.sort_values(by='가격', ascending=True).iloc[0]
            return f"<div class='price-font'>{min_row['가격']:,.0f}원</div><div class='small-font'>({min_row['판매처']}/{min_row['객실타입'][:10]})</div>"

        # 데이터 피벗
        detail_pivot = f_df.groupby(['호텔명', '날짜']).apply(get_min_detail).unstack()

        def color_signal(val):
            if val == "-" or amber_min_val == 0: return ''
            try:
                price_val = int(val.split('원')[0].split('>')[-1].replace(',', ''))
                if price_val < amber_min_val - 30000: return 'background-color: #ffcccc; color: #d32f2f;'
                if price_val < amber_min_val: return 'background-color: #fff3cd;'
                return 'background-color: #d4edda;'
            except: return ''

        # [지배인님 커스텀 포인트] CSS 주입
        st.markdown(f"""
            <style>
            /* 1. 테이블 레이아웃 고정 및 열 너비 조정 */
            table {{ 
                font-size: 11px !important; 
                table-layout: fixed !important; /* 열 너비를 고정함 */
                width: 100% !important; 
                border-collapse: collapse; 
            }}
            
            /* 2. 첫 번째 열(호텔명) 너비 설정 */
            th.row_heading {{ 
                width: 120px !important; 
                font-size: 11px !important;
                font-weight: 600 !important; /* 인덱스 두께 복구 */
                text-align: left !important;
                padding-left: 8px !important;
            }}

            /* 3. 데이터 열(날짜) 너비 설정 - 지배인님 여기서 숫자를 바꿔보세요 */
            th.col_heading, td {{ 
                width: 90px !important;  /* 가로 간격 조정 포인트 (기본 90px) */
                padding: 3px 2px !important; 
                line-height: 1.1 !important; 
                text-align: center !important;
            }}
            
            /* 4. 헤더 폰트 및 스타일 */
            th.col_heading {{ 
                font-size: 11px !important; 
                font-weight: 600 !important; /* 인덱스 두께 복구 */
                background-color: #f1f3f5 !important;
            }}
            
            .price-font {{ font-size: 11px; font-weight: 700; margin-bottom: -1px; }}
            .small-font {{ font-size: 8.5px !important; color: #777; line-height: 1.0 !important; }}
            </style>
        """, unsafe_allow_html=True)

        # HTML 렌더링
        st.write(detail_pivot.style.applymap(color_signal).to_html(escape=False), unsafe_allow_html=True)
        st.caption("※ 인덱스 가독성을 위해 두께를 복구했으며, 열 너비를 고정하여 간격을 최적화했습니다.")

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
        if not amber_df.empty:
            amber_pivot = amber_df.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
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
            comp_prices = comp_df['가격'].values
            if len(comp_prices) > 0:
                comb = np.append(comp_prices, sim_p); comb.sort()
                rank = np.where(comb == sim_p)[0][0] + 1
                st.write(f"🏆 예상 시장 순위: **{len(comb)}개 중 {rank}위**")
                st.progress((len(comb) - rank + 1) / len(comb))

        with st.expander("📋 상세 로그 보기"):
            st.dataframe(f_df.sort_values(['날짜', '수집시간_dt'], ascending=[True, False]), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"대시보드 에러 발생: {e}")
