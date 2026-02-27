import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from pathlib import Path

# 스트림릿 기본 스타일 숨기기
hide_streamlit_style = """
<style>
[data-testid="stAppToolbar"] {display: none;}
[data-testid="stHeader"] {display: none;}
footer {display: none;}
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 페이지 설정
st.set_page_config(
    page_title="BOB SSAFY",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한국 시간대 설정
KST = pytz.timezone("Asia/Seoul")

# 데이터 저장 디렉토리
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# CSS 스타일링 (원본 유지)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .menu-card {
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        background: rgba(255, 255, 255, 0.05);
    }
    .menu-corner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
    }
    .menu-image-container {
        width: 100%;
        height: 200px;
        border-radius: 15px;
        overflow: hidden;
        margin: 10px 0;
    }
    .menu-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .comment-box {
        background: rgba(102, 126, 234, 0.08);
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)

class WelplusAPI:
    def __init__(self):
        self.base_url = "https://welplus.welstory.com"
        self.device_id = "95CB2CC5-543E-4DA7-AD7D-3D2D463CB0A0"
        self.token = None
        self.headers = {
            "X-Device-Id": self.device_id,
            "X-Autologin": "Y",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Welplus/1.01.08",
        }

    def login(self, username, password):
        url = f"{self.base_url}/login"
        login_headers = self.headers.copy()
        login_headers.update({
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Authorization": "Bearer null",
        })
        data = {"username": username, "password": password, "remember-me": "true"}
        response = requests.post(url, headers=login_headers, data=data)
        if response.status_code == 200:
            self.token = response.headers.get("Authorization")
            return True
        return False

    def get_menu(self, date=None, meal_type="2"):
        if not self.token: return {"점심": [], "추가배식대": []}
        url = f"{self.base_url}/api/meal"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})
        if date is None: date = datetime.now(KST)
        menu_dt = date.strftime("%Y%m%d")
        params = {
            "menuDt": menu_dt, "menuMealType": meal_type,
            "restaurantCode": "REST000595", "sortingFlag": "",
            "mainDivRestaurantCode": "REST000595", "activeRestaurantCode": "REST000595",
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return self._parse_menu(response.json(), menu_dt)
        return {"점심": [], "추가배식대": []}

    def get_menu_rating(self, menu_dt, hall_no, menu_course_type, menu_meal_type, restaurant_code):
        if not self.token: return {"평균평점": 0, "참여자수": 0}
        url = f"{self.base_url}/api/meal/getMenuEvalAvg"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})
        params = {
            "menuDt": menu_dt, "hallNo": hall_no, "menuCourse_type": menu_course_type,
            "menuMealType": menu_meal_type, "restaurantCode": restaurant_code, "mainDivRestaurantCode": restaurant_code,
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {"평균평점": data.get("MENU_GRADE_AVG", 0), "참여자수": data.get("TOT_CNT", 0)}
        except: pass
        return {"평균평점": 0, "참여자수": 0}

    def _parse_menu(self, menu_data, menu_dt):
        """메뉴 파싱 (오류 수정: break 제거 및 추가배식대 분류)"""
        try:
            menu_items = []
            extra_items = []
            meal_list = menu_data.get("data", {}).get("mealList", [])

            for meal in meal_list:
                course_txt = meal.get("courseTxt", "")
                menu_name = meal.get("menuName", "")
                
                # 데이터 추출
                kcal = meal.get("sumKcal", "")
                sub_menu_txt = meal.get("subMenuTxt", "").split(",")
                photo_url = meal.get("photoUrl", "")
                photo_cd = meal.get("photoCd", "")
                image_url = f"{photo_url}{photo_cd}" if photo_url and photo_cd else None

                rating_info = self.get_menu_rating(
                    meal.get("menuDt"), meal.get("hallNo"),
                    meal.get("menuCourseType"), meal.get("menuMealType"),
                    meal.get("restaurantCode"),
                )

                info = {
                    "코너": course_txt, "메뉴명": menu_name, "칼로리": kcal,
                    "구성": sub_menu_txt, "이미지": image_url,
                    "평균평점": rating_info["평균평점"], "참여자수": rating_info["참여자수"],
                    "menu_id": f"{menu_dt}_{course_txt}_{menu_name}".replace(" ", "_"),
                }

                # 분류: SELF 또는 추가 배식대 여부 확인
                if "SELF" in course_txt or "추가" in course_txt:
                    extra_items.append(info)
                else:
                    menu_items.append(info)

            return {"점심": menu_items, "추가배식대": extra_items}
        except Exception as e:
            st.error(f"메뉴 파싱 중 오류: {e}")
            return {"점심": [], "추가배식대": []}

# --- 데이터 관리 (유지) ---
def load_data(filename, default):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return default

def save_data(filename, data):
    with open(DATA_DIR / filename, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def load_votes(): return load_data("votes.json", {})
def save_votes(votes): save_data("votes.json", votes)
def load_comments(): return load_data("comments.json", {})
def save_comments(comments): save_data("comments.json", comments)

# --- 화면 렌더링 ---
def render_menu_card(menu):
    """메인 메뉴 카드 디자인"""
    with st.container():
        st.markdown(f'<div class="menu-corner">{menu["코너"]}</div>', unsafe_allow_html=True)
        st.markdown(f"### {menu['메뉴명']}")
        if menu['이미지']:
            st.markdown(f'<div class="menu-image-container"><img src="{menu["이미지"]}" class="menu-image"></div>', unsafe_allow_html=True)
        st.markdown(f"🔥 **{menu['칼로리']} kcal**")
        st.caption(" · ".join(filter(None, menu['구성'])))
        
        # 투표 기능 (기존 유지)
        votes = load_votes()
        m_id = menu['menu_id']
        v_data = votes.get(m_id, {"좋아요": 0, "별로": 0})
        c1, c2 = st.columns(2)
        if c1.button(f"👍 {v_data['좋아요']}", key=f"L_{m_id}"):
            v_data['좋아요'] += 1; votes[m_id] = v_data; save_votes(votes); st.rerun()
        if c2.button(f"👎 {v_data['별로']}", key=f"D_{m_id}"):
            v_data['별로'] += 1; votes[m_id] = v_data; save_votes(votes); st.rerun()

def show_menu_page():
    if not st.session_state.get('api'):
        st.error("웰스토리 계정 설정이 필요합니다.")
        return

    selected_date = st.date_input("📅 날짜 선택", value=datetime.now(KST).date())
    menu_data = st.session_state.api.get_menu(date=selected_date)

    # 1. 메인 메뉴 (라면 제외)
    main_list = [m for m in menu_data["점심"] if "[라면" not in m["메뉴명"] and "마이보글" not in m["코너"]]
    if main_list:
        st.markdown("## 🍱 오늘의 메인 메뉴")
        cols = st.columns(len(main_list))
        for idx, m in enumerate(main_list):
            with cols[idx]: render_menu_card(m)

    # 2. 라면 코너
    ramen_list = [m for m in menu_data["점심"] if "[라면" in m["메뉴명"] or "마이보글" in m["코너"]]
    if ramen_list:
        st.divider()
        st.markdown("## 🍜 라면 코너")
        for r in ramen_list:
            st.markdown(f"**{r['코너']}**: {r['메뉴명']} ({r['칼로리']}kcal)")

    # 3. 추가 배식대 (SELF) - 새로 추가된 섹션
    if menu_data.get("추가배식대"):
        st.divider()
        st.markdown("## 🥗 추가 배식대 (SELF)")
        for extra in menu_data["추가배식대"]:
            with st.expander(f"➕ {extra['코너']} 상세 보기"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if extra['이미지']: st.image(extra['이미지'])
                with col2:
                    st.markdown(f"### {extra['메뉴명']}")
                    st.write(f"칼로리: {extra['칼로리']}kcal")
                    st.write(f"구성: {', '.join(extra['구성'])}")

def main():
    # 세션 관리 및 로그인 로직 (기존 secrets 활용 유지)
    if 'api' not in st.session_state:
        api = WelplusAPI()
        try:
            user = st.secrets["welstory"]["username"]
            pw = st.secrets["welstory"]["password"]
            if api.login(user, pw): st.session_state.api = api
        except: pass

    # 사이드바 (기존 유지)
    with st.sidebar:
        st.markdown("# 🍽️ BOB SSAFY")
        page = st.radio("메뉴", ["🍽️ 오늘의 메뉴", "📋 BOB HUB", "📊 통계"])
        
        # 광고 섹션 (기존 유지)
        st.divider()
        st.markdown("""
            <div style="background: #fff5f5; padding: 1rem; border-radius: 10px; border: 1px dashed #FF4B2B;">
                <h4 style="color: #FF4B2B; margin: 0;">📢 광고 문의</h4>
                <p style="font-size: 0.8rem;">jun394647@gmail.com</p>
            </div>
        """, unsafe_allow_html=True)

    if page == "🍽️ 오늘의 메뉴": show_menu_page()
    # 나머지 페이지 호출 (show_board_page 등 기존 함수들)

if __name__ == "__main__":
    main()
