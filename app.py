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
    
    # [우회 필살기 1] 자동화 제어 메시지 제거
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # [우회 필살기 2] 실제 윈도우 PC 브라우저처럼 보이게 위장
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    # [우회 필살기 3] 웹드라이버 흔적 지우기
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

st.title("🏨 앰버 AI 지배인: 그랜드 조선 제주 수집기")

target_date = st.sidebar.date_input("조회 날짜 선택", datetime(2026, 1, 25))
checkin = target_date.strftime("%Y-%m-%d")
checkout = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
hotel_id = "N5279751" 

if st.button('🚀 실시간 요금 수집 시작'):
    driver = get_driver()
    url = f"https://hotels.naver.com/detail/hotels/{hotel_id}/rates?checkIn={checkin}&checkOut={checkout}&adultCnt=2"
    
    try:
        with st.spinner(f'보안벽을 우회하여 데이터를 가져오는 중...'):
            driver.get(url)
            time.sleep(10) # 데이터 로딩을 위해 넉넉히 대기

            # 데이터를 찾기 위한 좀 더 강력한 방법
            # 클래스 이름이 미세하게 바뀌어도 찾을 수 있게 'Price'라는 글자가 포함된 모든 요소를 찾습니다.
            prices_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'Price_show')]")
            sellers_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'Price_seller')]")

            results = []
            for s, p in zip(sellers_elements, prices_elements):
                if s.text and p.text:
                    results.append({"판매처": s.text, "가격": p.text})

            if results:
                st.subheader(f"📊 수집 성공! ({target_date})")
                cols = st.columns(4)
                cols[0].metric("전체 최저가", results[0]['가격'])
                
                for r in results:
                    if "아고다" in r['판매처']: cols[1].metric("아고다", r['가격'])
                    if "트립닷컴" in r['판매처']: cols[2].metric("트립닷컴", r['가격'])
                    if "트립비토즈" in r['판매처']: cols[3].metric("트립비토즈", r['가격'])
                
                st.write("---")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.error("데이터 수집에 실패했습니다.")
                st.info("네이버가 로봇임을 감지하고 빈 화면을 보여준 것 같습니다.")
                # 디버깅을 위해 현재 화면에 어떤 텍스트가 있는지 확인
                st.text("현재 페이지 텍스트 일부:")
                st.write(driver.page_source[:500]) # 페이지 소스 앞부분 출력

    except Exception as e:
        st.error(f"오류 발생: {e}")
    finally:
        driver.quit()
