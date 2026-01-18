import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="앰버 AI 지배인", layout="wide")
st.title("🏨 앰버 AI 지배인: 스마트 데이터 수집 (Google 기반)")

# SerpApi 키를 그대로 사용합니다.
SERP_API_KEY = "여기에_본인의_API_KEY를_넣으세요"

target_date = st.sidebar.date_input("조회 날짜", datetime(2026, 1, 25))
checkin = target_date.strftime("%Y-%m-%d")

if st.button('🚀 데이터 배달 받기'):
    # 구글 검색을 통해 네이버 호텔 데이터를 타겟팅합니다.
    params = {
        "engine": "google",
        "q": f"그랜드 조선 제주 네이버 호텔 {checkin} 요금",
        "api_key": SERP_API_KEY
    }

    try:
        with st.spinner('구글을 통해 네이버 데이터를 추적 중...'):
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
            
            # 구글 검색 결과 중 '호텔 검색 결과(ads 또는 organic)'에서 가격 추출
            # SerpApi는 'shopping_results'나 'hotels_results' 형태로 데이터를 줍니다.
            hotels = data.get("ads", []) + data.get("organic_results", [])

            if hotels:
                st.success("✅ 관련 데이터를 찾았습니다!")
                
                # 검색 결과 요약 시각화
                for h in hotels[:3]: # 상위 3개 결과 출력
                    with st.expander(f"출처: {h.get('source', 'Google')}"):
                        st.write(f"**제목:** {h.get('title')}")
                        st.write(f"**설명:** {h.get('snippet')}")
                        if 'link' in h:
                            st.link_button("실제 페이지 보기", h['link'])

                st.info("💡 위 데이터에서 가격을 정밀 추출하는 로직을 추가 중입니다.")
            else:
                st.warning("데이터를 찾지 못했습니다. 키워드를 조정해 보세요.")

    except Exception as e:
        st.error(f"오류 발생: {e}")
