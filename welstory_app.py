import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="BOB SSAFY",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한국 시간대 설정
KST = pytz.timezone("Asia/Seoul")

# 데이터 저장 디렉토리
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# CSS 스타일링
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 가독성 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto+Sans+KR', sans-serif;
    }

    .main-header {
        font-size: clamp(1.8rem, 5vw, 2.8rem);
        font-weight: 900;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #FF4B2B 0%, #FF416C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 카드 높이 균일화 핵심 설정 */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    .menu-card {
        border: 2px solid rgba(255, 75, 43, 0.2);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        background: white;
        height: 100%; /* 카드 높이 100% */
        display: flex;
        flex-direction: column;
        transition: all 0.3s;
    }
    
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(255, 75, 43, 0.15);
        border-color: #FF4B2B;
    }
    
    .menu-header {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 1.2rem;
        min-height: 60px;
    }
    
    .menu-corner {
        background: #FF4B2B;
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
        white-space: nowrap;
    }
    
    .menu-name {
        font-size: clamp(1.1rem, 2vw, 1.4rem);
        font-weight: 800;
        line-height: 1.3;
        color: #333;
    }
    
    /* 이미지 크기 확대 */
    .menu-image {
        border-radius: 15px;
        width: 100%;
        height: 320px; 
        object-fit: cover;
        margin-bottom: 1rem;
    }
    
    .menu-info-row {
        font-size: 1rem;
        padding: 0.6rem;
        background: #fff5f5;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        color: #FF4B2B;
    }
    
    /* 성분이 길어져도 균형 유지 */
    .menu-ingredients {
        font-size: 0.95rem;
        line-height: 1.5;
        padding: 1rem;
        background: #fafafa;
        border-radius: 10px;
        border-left: 3px solid #FF4B2B;
        margin: 0.5rem 0;
        flex-grow: 1; /* 남은 공간 차지하여 높이 맞춤 */
        min-height: 80px;
    }
    
    .rating-section {
        background: linear-gradient(135deg, #FFD93D 0%, #FF6B35 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
    }

    /* 작은 화면 최적화 */
    @media (max-width: 768px) {
        .menu-card { padding: 1rem; }
        .menu-image { height: 220px; }
        .menu-name { font-size: 1.1rem; }
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
        try:
            response = requests.post(url, headers=login_headers, data=data)
            if response.status_code == 200:
                self.token = response.headers.get("Authorization")
                return True
        except: return False
        return False

    def get_menu(self, date=None, meal_type="2"):
        if not self.token: raise Exception("Not logged in")
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
        return {"점심": []}

    def get_menu_rating(self, menu_dt, hall_no, menu_course_type, menu_meal_type, restaurant_code):
        if not self.token: return {"평균평점": 0, "참여자수": 0}
        url = f"{self.base_url}/api/meal/getMenuEvalAvg"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})
        params = {
            "menuDt": menu_dt, "hallNo": hall_no, "menuCourseType": menu_course_type,
            "menuMealType": menu_meal_type, "restaurantCode": restaurant_code,
            "mainDivRestaurantCode": restaurant_code,
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {"평균평점": data.get("MENU_GRADE_AVG", 0), "참여자수": data.get("TOT_CNT", 0)}
        except: pass
        return {"평균평점": 0, "참여자수": 0}

    def _parse_menu(self, menu_data, menu_dt):
        try:
            menu_items = []
            meal_list = menu_data.get("data", {}).get("mealList", [])
            count = 0
            for meal in meal_list:
                if count >= 4 or meal.get("courseTxt") == "SELF 배식대": break
                
                photo_url = meal.get("photoUrl", "")
                photo_cd = meal.get("photoCd", "")
                image_url = f"{photo_url}{photo_cd}" if photo_url and photo_cd else None

                rating_info = self.get_menu_rating(
                    meal.get("menuDt"), meal.get("hallNo"), meal.get("menuCourseType"),
                    meal.get("menuMealType"), meal.get("restaurantCode")
                )

                menu_items.append({
                    "코너": meal.get("courseTxt", ""),
                    "메뉴명": meal.get("menuName", ""),
                    "칼로리": meal.get("sumKcal", ""),
                    "구성": meal.get("subMenuTxt", "").split(","),
                    "이미지": image_url,
                    "평균평점": rating_info["평균평점"],
                    "참여자수": rating_info["참여자수"],
                    "menu_id": f"{menu_dt}_{meal.get('courseTxt')}_{meal.get('menuName')}".replace(" ", "_"),
                })
                count += 1
            return {"점심": menu_items}
        except: return {"점심": []}

# 데이터 관리 함수
def load_data(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {} if "json" in filename else []

def save_data(filename, data):
    with open(DATA_DIR / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def display_menu_card(menu_item):
    """개별 메뉴 카드 렌더링"""
    st.markdown(f"""
    <div class="menu-card">
        <div class="menu-header">
            <span class="menu-corner">{menu_item['코너']}</span>
            <span class="menu-name">{menu_item['메뉴명']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if menu_item.get("이미지"):
        st.markdown(f'<img src="{menu_item["이미지"]}" class="menu-image">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:320px; background:#f0f0f0; border-radius:15px; display:flex; align-items:center; justify-content:center; color:#ccc; margin-bottom:1rem;">이미지 준비중</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="menu-info-row">🔥 {menu_item["칼로리"]} kcal</div>', unsafe_allow_html=True)
    
    if menu_item.get('평균평점', 0) > 0:
        st.markdown(f'<div class="rating-section">⭐ {menu_item["평균평점"]:.1f} ({menu_item["참여자수"]}명)</div>', unsafe_allow_html=True)
    
    ingredients = ", ".join(filter(None, menu_item['구성']))
    st.markdown(f'<div class="menu-ingredients">📋 {ingredients}</div>', unsafe_allow_html=True)

    # 투표 시스템
    votes = load_data("votes.json")
    mid = menu_item['menu_id']
    v_data = votes.get(mid, {"좋아요": 0, "별로": 0})
    
    col_l, col_d = st.columns(2)
    with col_l:
        if st.button(f"👍 좋아요 {v_data['좋아요']}", key=f"l_{mid}", use_container_width=True):
            v_data['좋아요'] += 1
            votes[mid] = v_data
            save_data("votes.json", votes)
            st.rerun()
    with col_d:
        if st.button(f"👎 별로 {v_data['별로']}", key=f"d_{mid}", use_container_width=True):
            v_data['별로'] += 1
            votes[mid] = v_data
            save_data("votes.json", votes)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_menu_page():
    st.markdown('<p class="main-header">🍱 BOB SSAFY 오늘의 메뉴</p>', unsafe_allow_html=True)
    
    if not st.session_state.get('logged_in'):
        st.error("BOB SSAFY 시스템에 연결할 수 없습니다. 설정을 확인해주세요.")
        return

    selected_date = st.date_input("📅 날짜 선택", value=datetime.now(KST).date())
    
    with st.spinner("맛있는 메뉴를 불러오는 중..."):
        menu_date = datetime.combine(selected_date, datetime.min.time()).replace(tzinfo=KST)
        menu_data = st.session_state.api.get_menu(date=menu_date)

    if not menu_data.get("점심"):
        st.info("해당 날짜에는 식단 정보가 없습니다.")
    else:
        cols = st.columns(min(len(menu_data["점심"]), 4))
        for idx, menu in enumerate(menu_data["점심"]):
            with cols[idx]:
                display_menu_card(menu)

def main():
    # Secrets 로드
    creds = st.secrets.get('welstory', {})
    if 'api' not in st.session_state:
        st.session_state.api = None
        st.session_state.logged_in = False

    if not st.session_state.logged_in and creds:
        api = WelplusAPI()
        if api.login(creds.get('username'), creds.get('password')):
            st.session_state.api = api
            st.session_state.logged_in = True

    # 사이드바
    with st.sidebar:
        st.markdown("<h1 style='text-align:center;'>🍱 BOB SSAFY</h1>", unsafe_allow_html=True)
        page = st.radio("이동", ["🍽️ 오늘의 메뉴", "📋 자유 게시판", "📊 메뉴 통계"])
        st.divider()
        st.caption("© 2026 BOB SSAFY Team")

    if page == "🍽️ 오늘의 메뉴": show_menu_page()
    elif page == "📋 자유 게시판": st.info("게시판 서비스 준비 중입니다.")
    elif page == "📊 메뉴 통계": st.info("통계 서비스 준비 중입니다.")

if __name__ == "__main__":
    main()
