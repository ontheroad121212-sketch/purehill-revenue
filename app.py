import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 전략 대시보드", layout="wide")

# 가독성과 직관성을 극대화하는 CSS 디자인
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1a1c1e; }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("정밀 시세 분석 및 150만원 이상 고가 객실 필터링 시스템 (v4.3)")

# 2. 데이터 로드 및 정제 함수
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # 10초마다 실시간 갱신
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        
        # [데이터 정밀 정제]
        # 1. 호텔명과 날짜 공백 정리
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['객실타입'] = data['객실타입'].astype(str).str.strip()
        
        # 2. 가격 숫자 변환 (콤마, 원 제거)
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        
        # 3. 수집시간 날짜 형식 변환
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        # 누락 데이터 제거
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        
        # [지배인님 요청 사항] 150만원 이상 고가 객실은 분석에서 제외 (상한 필터)
        data = data[data['가격'] < 1500000]
        
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- [사이드바 필터 구역] ---
        st.sidebar.header("🔍 분석 필터 설정")
        
        # 1. 날짜 멀티 선택
        all_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect("📅 분석 대상 날짜", options=all_dates, default=[all_dates[-1]] if all_dates else [])
        
        # 2. 지배인님의 13개 호텔 리스트 반영
        all_hotels = sorted(df['호텔명'].unique())
        target_list = [
            "엠버퓨어힐", "그랜드하얏트", "파르나스", "신라호텔", "롯데호텔", 
            "신라스테이", "해비치", "신화메리어트", "히든클리프", "더시에나", 
            "조선힐스위트", "메종글래드", "그랜드조선제주"
        ]
        selected_hotels = st.sidebar.multiselect("🏨 분석 대상 호텔", options=all_hotels, default=[h for h in target_list if h in all_hotels])

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
            # 1. 상단 핵심 지표 (150만원 미만 객실 기준)
            # ---------------------------------------------------------
            st.subheader("🚀 실시간 시장 지위 요약")
            amber_data = f_df[f_df['호텔명'].str.contains("엠버", na=False)]
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                if not amber_data.empty:
                    # 필터 내 엠버의 절대 최저가 추출
                    amber_min_price = amber_data['가격'].min()
                    amber_min_row = amber_data[amber_data['가격'] == amber_min_price].iloc[0]
                    st.metric("엠버 최저가", f"{amber_min_price:,.0f}원", 
                              help=f"객실: {amber_min_row['객실타입']} | 채널: {amber_min_row['판매처']}")
                else:
                    st.metric("엠버 최저가", "데이터 없음")
            
            with m_col2:
                # 시장 전체 최저가
                market_min_idx = f_df['가격'].idxmin()
                market_min_val = f_df.loc[market_min_idx, '가격']
                market_min_hotel = f_df.loc[market_min_idx, '호텔명']
                st.metric("시장 전체 최저가", f"{market_min_val:,.0f}원", help=f"최저가 호텔: {market_min_hotel}")

            with m_col3:
                # 시장 평균 대비 격차
                market_avg = f_df['가격'].mean()
                if not amber_data.empty:
                    diff_ratio = ((amber_min_price - market_avg) / market_avg) * 100
                    st.metric("시장 평균가 대비", f"{diff_ratio:+.1f}%", delta_color="inverse")
                else:
                    st.metric("시장 평균가 대비", "-")

            with m_col4:
                top_channel = f_df['판매처'].value_counts().idxmax()
                st.metric("최다 노출 채널", top_channel)

            st.markdown("---")

            # ---------------------------------------------------------
            # 2. 신호등 가격 매트릭스 (직관적 비교 표)
            # ---------------------------------------------------------
            st.subheader("🚦 일자별 호텔 최저가 매트릭스 (신호등)")
            
            pivot_df = f_df.groupby(['호텔명', '날짜'])['가격'].min().unstack()
            
            # 신호등 스타일 함수
            def color_signal(val):
                if pd.isna(val) or amber_data.empty: return ''
                ref_price = amber_min_price 
                diff = val - ref_price
                if diff < -30000: return 'background-color: #ffcccc; color: #d32f2f; font-weight: bold' 
                if diff < 0: return 'background-color: #fff3cd; color: #856404;' 
                return 'background-color: #d4edda; color: #155724;' 

            st.dataframe(pivot_df.style.format("{:,.0f}원", na_rep="-").applymap(color_signal), 
                         use_container_width=True)
            st.caption("💡 신호등 가이드: 빨강(경쟁사 저가 위협) / 노랑(경쟁사 약우세) / 초록(엠버 가격 경쟁력 우수)")

            st.markdown("---")

            # ---------------------------------------------------------
            # 3. 엠버 정밀 분석 (히트맵)
            # ---------------------------------------------------------
            col_a, col_b = st.columns([3, 2])
            
            with col_a:
                st.subheader("💎 엠버 객실별/채널별 최저가 분포 (Heatmap)")
                if not amber_data.empty:
                    amber_pivot = amber_data.pivot_table(index='객실타입', columns='판매처', values='가격', aggfunc='min')
                    fig_heat = px.imshow(amber_pivot, text_auto=',.0f', color_continuous_scale='RdYlGn_r', aspect="auto")
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.info("선택된 날짜/필터에 엠버 데이터가 없습니다.")

            with col_b:
                st.subheader("📊 호텔별 요금 분포 범위 (Box Plot)")
                fig_box = px.box(f_df, x="호텔명", y="가격", color="호텔명")
                fig_box.update_layout(showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)

            # ---------------------------------------------------------
            # 4. 수집 트렌드 및 상세 로그
            # ---------------------------------------------------------
            st.subheader("📉 수집 시점별 가격 변동 추이")
            fig_line = px.line(f_df.sort_values('수집시간'), x='수집시간', y='가격', 
                               color='호텔명', line_dash='날짜', markers=True,
                               hover_data=['판매처', '객실타입'])
            st.plotly_chart(fig_line, use_container_width=True)

            with st.expander("📋 상세 데이터 로그 확인 (150만원 미만 객실 전용)"):
                st.dataframe(f_df.sort_values(['날짜', '수집시간'], ascending=[True, False]), 
                             use_container_width=True, hide_index=True)

        else:
            st.warning("선택된 필터 조건에 데이터가 없거나 모든 객실이 150만원 이상입니다.")
    else:
        st.warning("구글 시트 데이터가 비어있습니다. 수집기를 먼저 실행해 주세요.")

except Exception as e:
    st.error(f"대시보드 구동 중 에러 발생: {e}")
