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
    # 실제 브라우저처럼 보이게 유저 에이전트 설정
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

st.title("🏨 앰버 AI 지배인: 그랜드 조선 제주 수집기")

# 1. 날짜 설정
target_date = st.sidebar.date_input("조회 날짜 선택", datetime(2026, 1, 25))
checkin = target_date.strftime("%Y-%m-%d")
checkout = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

# 2. 업데이트된 네이버 호텔 ID (보내주신 주소 기준)
hotel_id = "N5279751" 

if st.button('🚀 실시간 요금 수집 시작'):
    driver = get_driver()
    
    # [수정됨] 보내주신 최신 주소 형식으로 반영
    url = f"https://hotels.naver.com/detail/hotels/{hotel_id}/rates?checkIn={checkin}&checkOut={checkout}&adultCnt=2"
    
    try:
        with st.spinner(f'네이버 호텔 최신 주소로 접속 중...'):
            driver.get(url)
            
            # 알림창이 뜨면 무조건 닫기
            time.sleep(3)
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass 

            # 가격 리스트 로딩 대기
            time.sleep(8) 

            # 데이터 추출 (현재 네이버 호텔의 판매처와 가격 클래스)
            # 판매처와 가격을 한 번에 가져오기 위해 더 상위 요소인 '판매처 리스트'를 타겟팅합니다.
            items = driver.find_elements(By.CSS_SELECTOR, "li[class*='Price_item']")

            results = []
            for item in items:
                try:
                    seller = item.find_element(By.CSS_SELECTOR, "[class*='Price_seller']").text
                    price = item.find_element(By.CSS_SELECTOR, "[class*='Price_show']").text
                    if seller and price:
                        results.append({"판매처": seller, "가격": price})
                except:
                    continue

            if results:
                st.subheader(f"📊 수집 결과 ({target_date})")
                
                # 상단 메트릭 표시
                cols = st.columns(4)
                cols[0].metric("전체 최저가", results[0]['가격'])
                
                # 주요 채널만 골라서 표시
                for r in results:
                    if "아고다" in r['판매처']: cols[1].metric("아고다", r['가격'])
                    if "트립닷컴" in r['판매처']: cols[2].metric("트립닷컴", r['가격'])
                    if "트립비토즈" in r['판매처']: cols[3].metric("트립비토즈", r['가격'])
                
                st.write("---")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.error("데이터 수집에 실패했습니다.")
                st.info(f"현재 시도한 주소: {url}")
                st.write("네이버가 로봇 접속을 감지했을 수 있습니다. 잠시 후 다시 시도해 보세요.")

    except Exception as e:
        st.error(f"오류 발생: {e}")
    finally:
        driver.quit()
