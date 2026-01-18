import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import shutil

# 1. 셀레니움 브라우저 설정 (스트림릿 클라우드용)
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # 서버에 설치된 크롬 실행 파일의 위치를 자동으로 찾아냅니다.
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome_path:
        options.binary_location = chrome_path
    
    # 드라이버는 별도 설치 없이 시스템 것을 사용하도록 설정
    return webdriver.Chrome(options=options)

st.title("🏨 앰버 AI 지배인: 가격 수집기")

if st.button('🚀 데이터 수집 시작'):
    try:
        with st.spinner('서버 환경 확인 및 수집 중...'):
            driver = get_driver()
            driver.get("https://www.google.com") # 테스트용으로 먼저 구글 접속
            st.success(f"연결 성공! 브라우저 제목: {driver.title}")
            driver.quit()
    except Exception as e:
        st.error(f"작동 오류: {e}")

# 사이드바 설정
target_date = st.sidebar.date_input("체크인 날짜", datetime.now() + timedelta(days=1))
hotel_id = "1335035205" # 그랜드 조선 제주 고유 ID

if st.button('🚀 그랜드 조선 제주 가격 수집 시작'):
    driver = get_driver()
    checkin_str = target_date.strftime('%Y-%m-%d')
    checkout_str = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 네이버 호텔 검색 URL
    url = f"https://hotels.naver.com/hotels/{hotel_id}?checkIn={checkin_str}&checkOut={checkout_str}&adultCnt=2"
    
    try:
        with st.spinner('네이버 호텔 접속 중... (약 10~20초 소요)'):
            driver.get(url)
            # 가격 표가 나타날 때까지 최대 20초 대기
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "SearchList_SearchList__1S_i_")))
            
            st.success("데이터 로딩 완료!")
            
            # 요금 찾기 (네이버 호텔의 현재 구조에 맞춘 선택자 - 실제 사이트 구조 변경시 수정 필요)
            prices = driver.find_elements(By.CLASS_NAME, "Price_show__3_W0o")
            sellers = driver.find_elements(By.CLASS_NAME, "Price_seller__2L9m-")
            
            price_data = {}
            for seller, price in zip(sellers, prices):
                name = seller.text
                val = price.text
                if name in ["아고다", "트립닷컴", "트립비토즈"] or not price_data:
                    if "최저가" not in price_data:
                        price_data["최저가"] = val # 맨 처음 나오는게 보통 최저가
                    if name in ["아고다", "트립닷컴", "트립비토즈"]:
                        price_data[name] = val

            # 결과 화면 표시
            cols = st.columns(4)
            cols[0].metric("전체 최저가", price_data.get("최저가", "N/A"))
            cols[1].metric("아고다", price_data.get("아고다", "N/A"))
            cols[2].metric("트립닷컴", price_data.get("트립닷컴", "N/A"))
            cols[3].metric("트립비토즈", price_data.get("트립비토즈", "N/A"))

    except Exception as e:
        st.error(f"오류 발생: {e}")
    finally:
        driver.quit()

st.markdown(f"---")
st.caption("주의: 네이버 호텔 사이트의 구조가 변경되면 수집이 되지 않을 수 있습니다.")
