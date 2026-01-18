import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="앰버 AI 지배인", layout="wide")
st.title("🏨 앰버 AI 지배인: API 기반 가격 수집")

# 1. 설정 (여기에 본인의 API Key를 넣으세요)
SERP_API_KEY = "214ca90ef2550844357702354f7ee208b09d6caa86edfd40e4c1f08e74f511b5"

target_date = st.sidebar.date_input("조회 날짜 선택", datetime(2026, 1, 25))
checkin = target_date.strftime("%Y-%m-%d")
checkout = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

st.info(f"조회 대상: 그랜드 조선 제주 ({checkin} ~ {checkout})")

if st.button('🚀 실시간 요금 가져오기'):
    # SerpApi의 네이버 호텔 검색 파라미터
    params = {
        "engine": "naver_hotels",
        "hotel_id": "N5279751", # 그랜드 조선 제주
        "check_in": checkin,
        "check_out": checkout,
        "adults": "2",
        "api_key": SERP_API_KEY
    }

    try:
        with st.spinner('API 서버에서 데이터를 배달받는 중...'):
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
            
            # API 응답에서 가격 리스트 추출
            # SerpApi의 결과 구조에 따라 달라질 수 있습니다.
            prices = data.get("prices", [])

            if prices:
                st.success(f"✅ 성공적으로 {len(prices)}개의 판매처를 확인했습니다.")
                
                results = []
                for p in prices:
                    results.append({
                        "판매처": p.get("source"),
                        "가격": p.get("price")
                    })
                
                df = pd.DataFrame(results)
                
                # 대시보드 표시
                cols = st.columns(4)
                cols[0].metric("전체 최저가", f"{results[0]['가격']}")
                
                for r in results:
                    name = r['판매처']
                    if "Agoda" in name or "아고다" in name: cols[1].metric("아고다", r['가격'])
                    if "Trip.com" in name or "트립닷컴" in name: cols[2].metric("트립닷컴", r['가격'])
                    if "Tripbitoz" in name or "트립비토즈" in name: cols[3].metric("트립비토즈", r['가격'])

                st.write("---")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("이 날짜에는 판매 중인 객실이 없거나 데이터를 가져올 수 없습니다.")
                st.json(data) # 데이터 구조 확인용

    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {e}")
