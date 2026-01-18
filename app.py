import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="앰버 AI 지배인 통합 대시보드", layout="wide")

# 가독성을 높이기 위한 CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .css-1kyx0rg { background-color: #f0f2f6; } /* 사이드바 배경색 */
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.caption("멀티 날짜 비교 및 객실별 정밀 시세 분석 시스템")

# 2. 데이터 불러오기 및 정제
SHEET_ID = "1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    try:
        data = pd.read_csv(URL, encoding='utf-8-sig')
        # 데이터 정제
        data['호텔명'] = data['호텔명'].astype(str).str.replace(" ", "").str.strip()
        data['날짜'] = data['날짜'].astype(str).str.replace(" ", "").str.strip()
        data['가격'] = data['가격'].astype(str).str.replace(',', '').str.replace('원', '')
        data['가격'] = pd.to_numeric(data['가격'], errors='coerce')
        data['수집시간'] = pd.to_datetime(data['수집시간'], errors='coerce')
        
        # 객실타입 컬럼이 없으면 생성 (이전 데이터 호환용)
        if '객실타입' not in data.columns:
            data['객실타입'] = '일반'
            
        data = data.dropna(subset=['호텔명', '가격', '날짜'])
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

try:
    df = load_data()
    
    if not df.empty:
        # --- 사이드바 필터 ---
        st.sidebar.header("🔍 분석 필터")
        
        # [변경] 다중 날짜 선택 기능
        all_target_dates = sorted(df['날짜'].unique())
        selected_dates = st.sidebar.multiselect(
            "📅 비교할 날짜(들) 선택", 
            options=all_target_dates, 
            default=[all_target_dates[-1]] if all_target_dates else []
        )
        
        all_hotels = sorted(df['호텔명'].unique())
        default_selection = [h for h in all_hotels if "엠버" in h] + ["신라호텔", "그랜드하얏트", "파르나스"]
        default_selection = [h for h in default_selection if h in all_hotels]

        selected_hotels = st.sidebar.multiselect(
            "🏨 비교 호텔 선택", 
            options=all_hotels, 
            default=default_selection if default_selection else all_hotels[:4]
        )

        # 데이터 필터링 (선택된 날짜들 & 호텔들)
        filtered_df = df[(df['날짜'].isin(selected_dates)) & (df['호텔명'].isin(selected_hotels))]
        
        if not filtered_df.empty:
            # --- [신규 추가] 1. 엠버퓨어힐 핵심 객실별 요금 현황 (숫자로 직관적 확인) ---
            st.subheader("💎 엠버퓨어힐 주력 객실별 실시간 시세 (최신 수집 기준)")
            amber_only = filtered_df[filtered_df['호텔명'].str.contains("엠버", na=False)]
            
            if not amber_only.empty:
                # 엠버의 각 객실타입별 최신 수집 데이터만 추출
                amber_latest_list = []
                for r_type in ["힐엠버", "힐파인", "그린밸리"]:
                    r_df = amber_only[amber_only['객실타입'].str.contains(r_type, na=False)]
                    if not r_df.empty:
                        l_time = r_df['수집시간'].max()
                        amber_latest_list.append(r_df[r_df['수집시간'] == l_time])
                
                if amber_latest_list:
                    amber_display = pd.concat(amber_latest_list)
                    cols = st.columns(len(amber_display['객실타입'].unique()))
                    for idx, r_name in enumerate(amber_display['객실타입'].unique()):
                        r_val = amber_display[amber_display['객실타입'] == r_name]
                        with cols[idx]:
                            st.metric(f"{r_name} 최저가", f"{r_val['가격'].min():,.0f}원", 
                                      delta=f"판매처: {r_val.loc[r_val['가격'].idxmin(), '판매처']}")
            else:
                st.info("선택된 날짜에 엠버퓨어힐 데이터가 없습니다.")

            st.markdown("---")

            # --- [변경] 2. 상세 요금 표 (지배인님 요청: 호텔, 타입, 채널, 요금) ---
            st.subheader("📋 선택 날짜별 상세 요금 일람표")
            # 보기 편하게 날짜, 호텔, 요금 순으로 정렬
            table_df = filtered_df.sort_values(['날짜', '호텔명', '가격'], ascending=[True, True, True])
            
            # 표에 보여줄 컬럼 재구성
            st.dataframe(
                table_df[['날짜', '호텔명', '객실타입', '판매처', '가격', '수집시간']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # --- 3. 가격 변동 추이 그래프 ---
            st.subheader("📈 수집 시점별 가격 변동 히스토리")
            trend_data = filtered_df.groupby(['수집시간', '호텔명', '날짜'])['가격'].min().reset_index()
            # 여러 날짜가 섞일 경우를 위해 색상과 대시를 활용
            fig_trend = px.line(trend_data, x='수집시간', y='가격', color='호텔명', line_dash='날짜',
                                markers=True, title="날짜별/호텔별 최저가 추이")
            st.plotly_chart(fig_trend, use_container_width=True)

            # --- 4. 데이터 백업/다운로드 ---
            with st.expander("📥 전체 수집 데이터 보기 및 CSV 저장"):
                st.write(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("전체 데이터 다운로드", data=csv, file_name="amber_report.csv", mime='text/csv')

        else:
            st.warning("선택한 조건에 맞는 데이터가 없습니다. 사이드바 설정을 확인해 주세요.")
    else:
        st.warning("데이터가 비어 있습니다. 수집기(Collector.py)를 실행해 주세요.")

except Exception as e:
    st.error(f"대시보드 실행 중 오류 발생: {e}")
