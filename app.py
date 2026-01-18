import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="앰버 AI 지배인 대시보드", layout="wide")
st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")

SHEET_ID = "지배인님의_시트_ID"
URL = f"https://docs.google.com/spreadsheets/d/1gTbVR4lfmCVa2zoXwsOqjm1VaCy9bdGWYJGaifckqrs/gviz/tq?tqx=out:csv"

try:
    df = pd.read_csv(URL, encoding='utf-8')
    if not df.empty:
        # 날짜 필터 추가
        st.sidebar.header("📅 날짜 선택")
        selected_date = st.sidebar.selectbox("조회할 날짜를 선택하세요", options=sorted(df['날짜'].unique()))
        
        # 선택한 날짜 데이터만 추출
        filtered_df = df[df['날짜'] == selected_date]
        
        st.header(f"📊 {selected_date} 요금 현황")
        
        col1, col2 = st.columns(2)
        col1.metric("해당 날짜 최저가", f"{filtered_df['가격'].min():,.0f}원")
        col2.metric("수집된 상품 수", f"{len(filtered_df)}개")
        
        # 그래프: 객실별 가격 비교
        fig = px.bar(filtered_df, x='객실타입', y='가격', color='판매처', barmode='group', title=f"{selected_date} 플랫폼별 요금")
        st.plotly_chart(fig, use_container_width=True)
        
        # 전체 데이터 확인
        with st.expander("전체 수집 데이터 보기"):
            st.write(df)
    else:
        st.info("수집된 데이터가 없습니다.")
except Exception as e:
    st.error(f"오류: {e}")
