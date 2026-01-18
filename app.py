import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # [핵심] 스트림릿 서버 리눅스 환경의 표준 경로를 직접 지정합니다.
    options.binary_location = "/usr/bin/chromium"
    
    # 드라이버 위치도 직접 지정합니다. (packages.txt에서 깔아준 녀석)
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=options)

st.title("🏨 앰버 AI 지배인: 가격 수집기")

if st.button('🚀 데이터 수집 시작'):
    try:
        with st.spinner('서버 엔진 시동 중... (약 10초)'):
            driver = get_driver()
            driver.get("https://www.google.com")
            title = driver.title
            st.success(f"✅ 연결 성공! 브라우저가 '{title}' 페이지를 읽었습니다.")
            driver.quit()
    except Exception as e:
        st.error("🚨 수집 엔진을 실행하는 데 문제가 발생했습니다.")
        st.info("관리자 팁: packages.txt에 'chromium'과 'chromium-driver'가 있는지 확인해 주세요.")
        with st.expander("에러 상세 내용 보기"):
            st.write(e)
