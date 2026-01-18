import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

st.title("🏨 앰버 AI 지배인: 가격 수집기")

target_date = st.sidebar.date_input("조회 날짜", datetime(2026, 1, 25))
checkin, checkout = target_date.strftime("%Y-%m-%d"), (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

if st.button('🚀 실시간 요금 수집 시작'):
    driver = get_driver()
    url = f"https://hotels.naver.com/detail/hotels/N5279751/rates?checkIn={checkin}&checkOut={checkout}&adultCnt=2"
    
    try:
        with st.spinner('네이버 보안벽 우회 및 데이터 렌더링 대기 중...'):
            driver.get(url)
            
            # [핵심] 가격 요소가 나타날 때까지 최대 20초간 "지켜보기"
            wait = WebDriverWait(driver, 20)
            # 가격 판매처 클래스명(Price_seller)이 화면에 보일 때까지 대기
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='Price_seller']")))
            
            # 렌더링 직후 살짝 더 기다려주기
            time.sleep(2)

            sellers = driver.find_elements(By.CSS_SELECTOR, "[class*='Price_seller']")
            prices = driver.find_elements(By.CSS_SELECTOR, "[class*='Price_show']")

            results = [{"판매처": s.text, "가격": p.text} for s, p in zip(sellers, prices) if s.text and p.text]

            if results:
                st.success(f"✅ {len(results)}개의 요금을 찾았습니다!")
                cols = st.columns(4)
                cols[0].metric("전체 최저가", results[0]['가격'])
                for r in results:
                    if "아고다" in r['판매처']: cols[1].metric("아고다", r['가격'])
                    if "트립닷컴" in r['판매처']: cols[2].metric("트립닷컴", r['가격'])
                    if "트립비토즈" in r['판매처']: cols[3].metric("트립비토즈", r['가격'])
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.error("데이터 로딩은 성공했으나, 내용을 읽지 못했습니다.")

    except Exception as e:
        st.error(f"시간 초과 또는 오류: 네이버가 평소보다 느리거나 로봇을 강하게 차단 중입니다.")
        st.info("재시도 버튼을 한 번 더 눌러보세요.")
    finally:
        driver.quit()
