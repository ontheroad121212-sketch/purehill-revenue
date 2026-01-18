import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="앰버 AI 지배인 대시보드", layout="wide")

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.markdown("---")

# 구글 시트 불러오기 (시트 ID를 입력하세요)
SHEET_ID = "지배인님의_구글시트_ID"
URL = f"https://docs.google.com/spreadsheets/d/1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs/gviz/tq?tqx=out:csv"

try:
    # 데이터 로드
    df = pd.read_csv(URL)
    
    # 데이터가 있을 때만 실행
    if not df.empty:
        # 1. 상단 메트릭 (주요 지표)
        min_price = df['가격'].min()
        avg_price = df['가격'].mean()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("현재 최저가", f"{min_price:,.0f}원")
        col2.metric("평균 판매가", f"{avg_price:,.0f}원")
        col3.metric("최근 업데이트", df['수집시간'].iloc[-1])
        
        st.markdown("---")
        
        # 2. 가격 분포 그래프
        st.subheader("📈 객실별 가격 분포")
        fig = px.bar(df, x='객실타입', y='가격', color='판매처', barmode='group',
                     title="플랫폼별/객실별 실시간 요금 비교")
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. 상세 데이터 테이블
        st.subheader("📋 상세 요금 리스트")
        # 가격 순으로 정렬해서 보여주기
        st.dataframe(df.sort_values(by="가격"), use_container_width=True)
        
    else:
        st.info("데이터베이스가 비어 있습니다. Collector.py를 실행하여 데이터를 수집해 주세요.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
