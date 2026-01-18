import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

st.title("🏨 앰버 AI 지배인: 가격 수집기")

# 1. 날짜 설정 (하이픈 없는 형식을 위해 포맷 변경)
target_date = st.sidebar.date_input("조회 날짜 선택", datetime.now() + timedelta(days=7))
checkin_str = target_date.strftime("%Y%m%d") # 예: 20260125
checkout_str = (target_date + timedelta(days=1)).strftime("%Y%m%d")

hotel_id = "1335035205" # 그랜드 조선 제주

if st.button('🚀 그랜드 조선 제주 가격 수집 시작'):
    driver = get_driver()
    
    # 네이버 호텔 최신 주소 형식 (YYYYMMDD 방식)
    url = f"https://hotels.naver.com/hotels/{hotel_id}?checkIn={checkin_str}&checkOut={checkout_str}&adultCnt=2"
    
    try:
        with st.spinner(f'{target_date} 데이터를 읽어오는 중...'):
            driver.get(url)
            
            # 혹시 모를 팝업이나 알림창 자동 닫기 시도
            try:
                alert = driver.switch_to.alert
                alert.accept() # 알림창이 뜨면 확인 버튼 누름
            except:
                pass 

            time.sleep(8) # 충분한 로딩 대기

            # 데이터 추출
            sellers = driver.find_elements(By.CLASS_NAME, "Price_seller__2L9m-")
            prices = driver.find_elements(By.CLASS_NAME, "Price_show__3_W0o")

            results = []
            for s, p in zip(sellers, prices):
                results.append({"판매처": s.text, "가격": p.text})

            if results:
                st.subheader(f"📊 수집 결과 ({target_date})")
                cols = st.columns(4)
                cols[0].metric("전체 최저가", results[0]['가격'])
                
                # 채널별 데이터 매칭
                for item in results:
                    if "아고다" in item['판매처']: cols[1].metric("아고다", item['가격'])
                    if "트립닷컴" in item['판매처']: cols[2].metric("트립닷컴", item['가격'])
                    if "트립비토즈" in item['판매처']: cols[3].metric("트립비토즈", item['가격'])
                
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.warning("가격 데이터를 찾지 못했습니다. 네이버 페이지 구조가 바뀌었을 수 있습니다.")
                st.info(f"수집 시도 주소: {url}")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
    finally:
        driver.quit()
