import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
from pathlib import Path

# ---------------------------
# Streamlit UI 숨기기
# ---------------------------
hide_streamlit_style = """
<style>
[data-testid="stAppToolbar"] {display: none;}
[data-testid="stHeader"] {display: none;}
footer {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 페이지 설정
# ---------------------------
st.set_page_config(
    page_title="BOB SSAFY",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# 시간 설정
# ---------------------------
KST = pytz.timezone("Asia/Seoul")

# ---------------------------
# 데이터 폴더
# ---------------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------
# 사이드바 날짜 상태 초기화
# ---------------------------
today = datetime.now(KST).date()

if "selected_date" not in st.session_state:
    st.session_state.selected_date = today


# ---------------------------
# API 클래스
# ---------------------------
class WelplusAPI:

    def __init__(self):

        self.base_url = "https://welplus.welstory.com"

        self.device_id = "device"

        self.token = None

        self.headers = {

            "X-Device-Id": self.device_id,

            "X-Autologin": "Y",

        }


    def login(self, username, password):

        url = f"{self.base_url}/login"

        headers = self.headers.copy()

        headers.update({

            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",

            "Authorization": "Bearer null",

        })

        data = {

            "username": username,

            "password": password,

            "remember-me": "true"

        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:

            self.token = response.headers.get("Authorization")

            return True

        return False


    def get_menu(self, date=None):

        if not self.token:

            return {"점심": []}

        url = f"{self.base_url}/api/meal"

        headers = self.headers.copy()

        headers.update({"Authorization": self.token})

        if date is None:

            date = datetime.now(KST)

        params = {

            "menuDt": date.strftime("%Y%m%d"),

            "menuMealType": "2",

            "restaurantCode": "REST000595",

        }

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:

            return {"점심": res.json().get("data", {}).get("mealList", [])}

        return {"점심": []}


# ---------------------------
# 메뉴 페이지
# ---------------------------
def show_menu_page():

    selected_date = st.session_state.selected_date

    st.markdown(f"## 📅 {selected_date.strftime('%Y년 %m월 %d일')} 메뉴")

    if "api" not in st.session_state:

        st.warning("로그인 필요")

        return

    menu_date = datetime.combine(selected_date, datetime.min.time())

    menu_date = KST.localize(menu_date)

    menu_data = st.session_state.api.get_menu(menu_date)

    if not menu_data["점심"]:

        st.info("메뉴 없음")

        return

    cols = st.columns(4)

    for i, menu in enumerate(menu_data["점심"][:4]):

        with cols[i]:

            st.write(menu.get("menuName", ""))


# ---------------------------
# 게시판 페이지
# ---------------------------
def show_board_page():

    st.title("게시판")


# ---------------------------
# 통계 페이지
# ---------------------------
def show_stats_page():

    st.title("통계")


# ---------------------------
# 메인
# ---------------------------
def main():

    # 자동 로그인

    if "api" not in st.session_state:

        api = WelplusAPI()

        # secrets 사용 시 수정

        st.session_state.api = api


    # ---------------------------
    # 사이드바
    # ---------------------------
    with st.sidebar:

        st.title("🍽️ BOB SSAFY")

        # ⭐ 날짜 선택 (사이드바 전용)
        selected_date = st.date_input(

            "📅 날짜 선택",

            value=st.session_state.selected_date,

            min_value=today,

            max_value=today + timedelta(days=7)

        )

        st.session_state.selected_date = selected_date


        st.divider()


        page = st.radio(

            "페이지",

            ["🍽️ 오늘의 메뉴", "📋 게시판", "📊 통계"]

        )


    # ---------------------------
    # 페이지 라우팅
    # ---------------------------
    if page == "🍽️ 오늘의 메뉴":

        show_menu_page()

    elif page == "📋 게시판":

        show_board_page()

    else:

        show_stats_page()


# ---------------------------
# 실행
# ---------------------------
if __name__ == "__main__":

    main()
