import streamlit as st
import pandas as pd

st.title("🏨 앰버 AI 지배인: 실시간 대시보드")

# 구글 시트 URL (CSV 출력 주소로 변환 필요)
SHEET_URL = "여기에_구글시트_CSV_공유주소"

if st.button('📈 최신 데이터 불러오기'):
    try:
        # 구글 시트에서 데이터 읽기
        df = pd.read_csv(SHEET_URL)
        st.success("데이터베이스 연결 성공!")
        
        # 가장 최근 데이터 한 줄 가져오기
        latest = df.iloc[-1]
        
        cols = st.columns(4)
        cols[0].metric("전체 최저가", latest['최저가'])
        cols[1].metric("아고다", latest['아고다'])
        cols[2].metric("트립닷컴", latest['트립닷컴'])
        cols[3].metric("트립비토즈", latest['트립비토즈'])
        
        st.write("### 가격 변동 히스토리")
        st.line_chart(df.set_index('수집시간')['최저가']) # 간단한 그래프
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"데이터를 불러올 수 없습니다: {e}")
