import streamlit as st
import pandas as pd

st.set_page_config(page_title="앰버 AI 지배인", layout="wide")

st.title("🏨 앰버 7대 플랫폼 통합 AI 지배인")
st.subheader("실시간 가격 전략 및 리뷰 관리")

# 메뉴 구성
menu = ["홈", "경쟁사 모니터링", "동적 가격 제안", "AI 리뷰 답글"]
choice = st.sidebar.selectbox("메뉴 선택", menu)

if choice == "홈":
    st.write("반갑습니다! 호텔 세일즈 자동화 시스템입니다.")
    st.info("왼쪽 메뉴를 선택하여 업무를 시작하세요.")

elif choice == "동적 가격 제안":
    st.header("📈 수요 기반 가격 전략")
    occ = st.slider("현재 예상 점유율(%)", 0, 100, 50)
    base_price = 150000

    # 간단한 로직: 점유율이 80% 넘으면 가격 20% 인상
    if occ > 80:
        suggested = base_price * 1.2
        st.success(f"수요가 높습니다! 추천 가격: {int(suggested):,}원")
    else:
        st.info(f"정상 수요입니다. 추천 가격: {base_price:,}원")
