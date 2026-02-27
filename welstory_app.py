import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from pathlib import Path

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

# CSS 스타일링 (기본 rast_app.py 디자인 유지)
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
        transition: transform 0.3s, box-shadow 0.3s;
        background: rgba(255, 255, 255, 0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .menu-corner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        white-space: nowrap;
    }
    .menu-image-container {
        width: 100%;
        height: 200px;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .menu-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .menu-rating-small {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: linear-gradient(135deg, #FFD93D 0%, #FF6B35 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .menu-calories {
        font-size: 1rem;
        font-weight: bold;
        color: #667eea;
        margin-top: 0.8rem;
        padding: 0.5rem;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 8px;
        text-align: center;
    }
    .menu-ingredients {
        font-size: 0.9rem;
        line-height: 1.8;
        padding: 1rem;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-top: 1rem;
    }
    .ingredient-item {
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(102, 126, 234, 0.1);
    }
    .comment-box {
        background: rgba(102, 126, 234, 0.08);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border-left: 4px solid #667eea;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
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
        login_headers.update({"Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "Authorization": "Bearer null"})
        data = {"username": username, "password": password, "remember-me": "true"}
        response = requests.post(url, headers=login_headers, data=data)
        if response.status_code == 200:
            self.token = response.headers.get("Authorization")
            return True
        return False

    def get_menu(self, date=None, meal_type="2"):
        if not self.token: raise Exception("Not logged in")
        url = f"{self.base_url}/api/meal"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})
        if date is None: date = datetime.now(KST)
        menu_dt = date.strftime("%Y%m%d")
        params = {"menuDt": menu_dt, "menuMealType": meal_type, "restaurantCode": "REST000595", "sortingFlag": "", "mainDivRestaurantCode": "REST000595", "activeRestaurantCode": "REST000595"}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return self._parse_menu(response.json(), menu_dt)
        return {"점심": [], "추가배식대": []}

    def get_menu_rating(self, menu_dt, hall_no, menu_course_type, menu_meal_type, restaurant_code):
        if not self.token: return {"평균평점": 0, "참여자수": 0}
        url = f"{self.base_url}/api/meal/getMenuEvalAvg"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})
        params = {"menuDt": menu_dt, "hallNo": hall_no, "menuCourseType": menu_course_type, "menuMealType": menu_meal_type, "restaurantCode": restaurant_code, "mainDivRestaurantCode": restaurant_code}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {"평균평점": data.get("MENU_GRADE_AVG", 0), "참여자수": data.get("TOT_CNT", 0)}
        except: pass
        return {"평균평점": 0, "참여자수": 0}

    def _parse_menu(self, menu_data, menu_dt):
        """메뉴 파싱 (일반/라면/추가배식대 별도 분류)"""
        try:
            regular_items = []
            ramen_items = []
            extra_items = []
            meal_list = menu_data.get("data", {}).get("mealList", [])

            for meal in meal_list:
                course_txt = meal.get("courseTxt", "")
                menu_name = meal.get("menuName", "")
                
                # 공통 정보 파싱
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

                # 분류 로직 (기존 break 제거 및 정교화)
                if "SELF" in course_txt or "추가" in course_txt:
                    extra_items.append(info)
                elif "마이보글" in course_txt or "[라면" in menu_name:
                    ramen_items.append(info)
                else:
                    # 메인 메뉴 (최대 4개 제한 유지 가능하나, API 모든 데이터 수집 위해 제한 해제 권장)
                    regular_items.append(info)

            return {"점심": regular_items, "라면": ramen_items, "추가배식대": extra_items}
        except Exception as e:
            st.error(f"메뉴 파싱 오류: {str(e)}")
            return {"점심": [], "라면": [], "추가배식대": []}

# 데이터 관리 함수 (원본 코드 유지)
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
def load_board_posts(): return load_data("board.json", [])
def save_board_posts(posts): save_data("board.json", posts)

def get_welstory_credentials():
    try:
        if hasattr(st, 'secrets') and 'welstory' in st.secrets:
            return {'username': st.secrets['welstory']['username'], 'password': st.secrets['welstory']['password']}
    except: pass
    return {}

# 카드 렌더링 함수 (디자인 코드 통합 유지)
def render_menu_card(menu):
    """메인 메뉴 카드 렌더링 (기존 rast_app.py 코드와 동일한 레이아웃)"""
    with st.container():
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.8rem; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 2px solid rgba(102, 126, 234, 0.2);">
            <div class="menu-corner">{menu['코너']}</div>
            <div style="font-size: 1.2rem; font-weight: 700; line-height: 1.3; text-align: center; color: #667eea;">{menu['메뉴명']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if menu.get("이미지"):
            st.markdown(f'<div class="menu-image-container"><img src="{menu["이미지"]}" class="menu-image"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="menu-image-container"><div class="menu-image-placeholder">이미지 없음</div></div>', unsafe_allow_html=True)
        
        if menu.get('평균평점', 0) > 0:
            st.markdown(f'<div class="menu-rating-small">⭐ {menu["평균평점"]:.1f} ({menu["참여자수"]}명)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="menu-rating-small">⭐ (평가 없음)</div>', unsafe_allow_html=True)
            
        st.markdown(f'<div class="menu-calories">🔥 {menu["칼로리"]}kcal</div>', unsafe_allow_html=True)
        
        if menu['구성']:
            ingredients_items = ''.join([f'<div class="ingredient-item">• {ing}</div>' for ing in menu['구성'] if ing])
            st.markdown(f'<div class="menu-ingredients" style="min-height: 150px; max-height: 150px; overflow-y: auto;">📋 <strong>구성</strong><br>{ingredients_items}</div>', unsafe_allow_html=True)
        
        # 투표 기능
        votes = load_votes()
        m_id = menu['menu_id']
        v_data = votes.get(m_id, {"좋아요": 0, "별로": 0})
        col1, col2 = st.columns(2)
        if col1.button(f"👍 {v_data['좋아요']}", key=f"L_{m_id}", use_container_width=True):
            v_data['좋아요'] += 1; votes[m_id] = v_data; save_votes(votes); st.rerun()
        if col2.button(f"👎 {v_data['별로']}", key=f"D_{m_id}", use_container_width=True):
            v_data['별로'] += 1; votes[m_id] = v_data; save_votes(votes); st.rerun()
        
        # 댓글 기능
        with st.expander("💬 댓글 보기/작성"):
            comments = load_comments()
            m_comments = comments.get(m_id, [])
            for c in m_comments:
                st.markdown(f'<div class="comment-box"><strong>{c["author"]}</strong> <small>{c["timestamp"]}</small><br>{c["text"]}</div>', unsafe_allow_html=True)
            with st.form(key=f"F_{m_id}"):
                c1, c2 = st.columns([1, 3])
                author = c1.text_input("이름", key=f"A_{m_id}", placeholder="익명")
                text = c2.text_input("댓글", key=f"T_{m_id}")
                if st.form_submit_button("작성", use_container_width=True) and text:
                    if m_id not in comments: comments[m_id] = []
                    comments[m_id].append({"author": author or "익명", "text": text, "timestamp": datetime.now(KST).strftime("%H:%M")})
                    save_comments(comments); st.rerun()

def show_menu_page():
    if 'api' not in st.session_state or st.session_state.api is None:
        st.warning("⚠️ API 연결 필요")
        return

    selected_date = st.date_input("📅 날짜 선택", value=datetime.now(KST).date())

    try:
        with st.spinner("로딩 중..."):
            menu_date = KST.localize(datetime.combine(selected_date, datetime.min.time()))
            data = st.session_state.api.get_menu(date=menu_date)

        if not data["점심"] and not data["라면"] and not data["추가배식대"]:
            st.warning("메뉴가 없습니다.")
            return

        # 1. 메인 메뉴 표시
        if data["점심"]:
            st.markdown("### 🍱 메인 메뉴")
            cols = st.columns(min(len(data["점심"]), 4))
            for i, m in enumerate(data["점심"]):
                with cols[i % len(cols)]: render_menu_card(m)

        # 2. 라면 메뉴 표시
        if data["라면"]:
            st.markdown("---")
            st.markdown("### 🍜 라면 코너")
            for r in data["라면"]:
                with st.container():
                    st.markdown(f"**{r['코너']}**: {r['메뉴명']} ({r['칼로리']}kcal)")
                    st.caption(" · ".join(filter(None, r['구성'])))

        # 3. 추가 배식대 (SELF) 표시 - 요구사항 반영
        if data["추가배식대"]:
            st.markdown("---")
            st.markdown("### 🥗 추가 배식대 (SELF)")
            for extra in data["추가배식대"]:
                with st.expander(f"➕ {extra['코너']} : {extra['메뉴명']}"):
                    col1, col2 = st.columns([1, 2])
                    if extra['이미지']: col1.image(extra['이미지'])
                    col2.write(f"**칼로리:** {extra['칼로리']}kcal")
                    col2.write(f"**구성:** {', '.join(filter(None, extra['구성']))}")

    except Exception as e: st.error(f"오류: {e}")

# --- 게시판, 통계, 메인 함수 (원본 rast_app.py와 100% 동일 유지) ---
def show_board_page():
    st.markdown('<p class="main-header">📋 BOB HUB</p>', unsafe_allow_html=True)
    posts = load_board_posts()
    if st.button("✍️ 새 글 작성", type="primary"): st.session_state.writing = True
    if st.session_state.get('writing'):
        with st.form("new_post"):
            title = st.text_input("제목")
            author = st.text_input("작성자")
            content = st.text_area("내용")
            if st.form_submit_button("작성") and title and content:
                posts.insert(0, {"id": len(posts), "title": title, "author": author or "익명", "content": content, "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), "comments": []})
                save_board_posts(posts); st.session_state.writing = False; st.rerun()
    for post in posts:
        with st.expander(f"{post['title']} - {post['author']}"):
            st.write(post['content'])

def show_stats_page():
    st.markdown('<p class="main-header">📊 메뉴 통계</p>', unsafe_allow_html=True)
    votes = load_votes()
    if votes:
        total_l = sum(v['좋아요'] for v in votes.values())
        st.metric("총 좋아요 👍", total_l)

def main():
    credentials = get_welstory_credentials()
    if 'api' not in st.session_state:
        st.session_state.api = None
        if credentials:
            api = WelplusAPI()
            if api.login(credentials['username'], credentials['password']): st.session_state.api = api

    with st.sidebar:
        st.markdown("## 🍽️ BOB SSAFY")
        page = st.radio("페이지 선택", ["🍽️ 오늘의 메뉴", "📋 BOB HUB", "📊 통계"], label_visibility="collapsed")
        
        # 광고 모집 섹션 (디자인 유지)
        google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdAkULzHhKYs8vQPmiHotxzpWluN6zvAkqS3gv-zV5pG85d9Q/viewform?usp=publish-editor"
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff5f5 0%, #fff0f0 100%); padding: 1.2rem; border-radius: 15px; border: 1px dashed #FF4B2B; margin-top: 2rem;">
                <h4 style="color: #FF4B2B; margin-top: 0;">📢 광고/제휴 모집</h4>
                <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">준비된 파트너를 찾고 있습니다.<br>문의: jun394647@gmail.com</p>
                <a href="{google_form_url}" target="_blank" style="text-decoration: none;">
                    <div style="background: #FF4B2B; color: white; text-align: center; padding: 0.6rem; border-radius: 8px; font-weight: bold;">제안서 보내기</div>
                </a>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.caption("© 2026 BOB SSAFY Team")

    if page == "🍽️ 오늘의 메뉴": show_menu_page()
    elif page == "📋 BOB HUB": show_board_page()
    elif page == "📊 통계": show_stats_page()

if __name__ == "__main__":
    main()
