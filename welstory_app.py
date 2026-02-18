import streamlit as st
from datetime import datetime, timedelta
import pytz

# timezone 설정
KST = pytz.timezone("Asia/Seoul")

# -------------------------
# 사이드바
# -------------------------
def sidebar():

    st.sidebar.title("📅 날짜 선택")

    today = datetime.now().astimezone(KST).date()

    st.sidebar.date_input(
        "날짜 선택",
        value=today,
        min_value=today,
        max_value=today + timedelta(days=7),
        key="selected_date"
    )


# -------------------------
# 메뉴 페이지
# -------------------------
def show_menu_page():

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now().astimezone(KST).date()

    selected_date = st.session_state.selected_date

    st.title("🍽️ 점심 메뉴")

    st.markdown(
        f"### 📅 {selected_date.strftime('%Y년 %m월 %d일')}"
    )

    # date → datetime 변환 (안정 버전)
    menu_date = datetime.combine(
        selected_date,
        datetime.min.time(),
        tzinfo=KST
    )

    # 테스트 출력
    st.write("API 전달 날짜:", menu_date)

    # 실제 사용 시
    # menu_data = st.session_state.api.get_menu(menu_date)

    st.success("정상 작동")


# -------------------------
# 메인
# -------------------------
def main():

    sidebar()

    show_menu_page()


# -------------------------
# 실행
# -------------------------
if __name__ == "__main__":
    main()
