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

st.title("🏨 앰버 AI 지배인: 실시간 가격 수집")

# 1. 날짜 선택 기능
target_date = st.sidebar.date_input("조회 날짜 선택", datetime.now() + timedelta(days=7))
checkin = target_date.strftime("%Y-%m-%d")
checkout = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

if st.button('🚀 그랜드 조선 제주 가격 수집 시작'):
    driver = get_driver()
    # 그랜드 조선 제주 고유 번호가 포함된 네이버 호텔 주소
    url = f"https://hotels.naver.com/hotels/1335035205?checkIn={checkin}&checkOut={checkout}&adultCnt=2"
    
    try:
        with st.spinner(f'{target_date} 요금 데이터를 수집 중입니다...'):
            driver.get(url)
            time.sleep(7) # 네이버 가격표가 뜰 때까지 충분히 기다림 (중요!)

            # 가격과 판매처 정보 찾기
            # 네이버 호텔의 현재 구조(클래스 이름)를 기반으로 데이터를 추출합니다.
            sellers = driver.find_elements(By.CLASS_NAME, "Price_seller__2L9m-")
            prices = driver.find_elements(By.CLASS_NAME, "Price_show__3_W0o")

            results = []
            for s, p in zip(sellers, prices):
                results.append({"판매처": s.text, "가격": p.text})

            if results:
                df = pd.DataFrame(results)
                
                # 우리가 원하는 4가지 정보 필터링
                st.subheader(f"📊 수집 결과 ({target_date})")
                
                # 대시보드 형태 시각화
                cols = st.columns(4)
                
                # 전체 최저가 (가장 첫 번째 데이터)
                cols[0].metric("전체 최저가", results[0]['가격'])
                
                # 특정 채널 찾기
                for item in results:
                    if "아고다" in item['판매처']:
                        cols[1].metric("아고다", item['가격'])
                    if "트립닷컴" in item['판매처']:
                        cols[2].metric("트립닷컴", item['가격'])
                    if "트립비토즈" in item['판매처']:
                        cols[3].metric("트립비토즈", item['가격'])

                st.write("---")
                st.write("전체 요금 리스트")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("데이터를 찾지 못했습니다. 날짜를 변경하거나 잠시 후 다시 시도해 주세요.")

    except Exception as e:
        st.error(f"오류 발생: {e}")
    finally:
        driver.quit()
