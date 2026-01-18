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
    # 네이버의 자동화 탐지를 피하기 위한 유저 에이전트 추가
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

st.title("🏨 앰버 AI 지배인: 가격 수집기")

# 1. 날짜 설정 (네이버가 좋아하는 YYYY-MM-DD 형식으로 일단 시도)
target_date = st.sidebar.date_input("조회 날짜 선택", datetime.now() + timedelta(days=7))
checkin = target_date.strftime("%Y-%m-%d")
checkout = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

hotel_id = "1335035205" # 그랜드 조선 제주

if st.button('🚀 그랜드 조선 제주 가격 수집 시작'):
    driver = get_driver()
    
    # 네이버 호텔 최신 주소 규격
    url = f"https://hotels.naver.com/hotels/{hotel_id}?checkIn={checkin}&checkOut={checkout}&adultCnt=2"
    
    try:
        with st.spinner(f'네이버 호텔 분석 중...'):
            driver.get(url)
            
            # [핵심] 알림창(유효하지 않은 경로)이 뜨면 자동으로 닫기
            time.sleep(3)
            try:
                alert = driver.switch_to.alert
                st.warning(f"네이버 알림 발생: {alert.text} (무시하고 진행 시도)")
                alert.accept()
            except:
                pass 

            # 페이지 로딩 대기
            time.sleep(7) 

            # 가격 정보 추출 (클래스 이름이 바뀌었을 것에 대비해 좀 더 범용적인 방법 사용)
            sellers = driver.find_elements(By.CSS_SELECTOR, "[class*='Price_seller']")
            prices = driver.find_elements(By.CSS_SELECTOR, "[class*='Price_show']")

            results = []
            for s, p in zip(sellers, prices):
                if s.text and p.text:
                    results.append({"판매처": s.text, "가격": p.text})

            if results:
                st.subheader(f"📊 수집 결과 ({target_date})")
                cols = st.columns(4)
                cols[0].metric("전체 최저가", results[0]['가격'])
                
                for item in results:
                    if "아고다" in item['판매처']: cols[1].metric("아고다", item['가격'])
                    if "트립닷컴" in item['판매처']: cols[2].metric("트립닷컴", item['가격'])
                    if "트립비토즈" in item['판매처']: cols[3].metric("트립비토즈", item['가격'])
                
                st.table(pd.DataFrame(results))
            else:
                st.error("데이터를 찾지 못했습니다. 네이버의 자동 수집 방어벽에 걸렸을 수 있습니다.")
                st.info(f"접속 시도한 주소: {url}")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
    finally:
        driver.quit()
