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

# CSS 스타일링
st.markdown("""
    <style>
    /* 다크모드/라이트모드 대응 */
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
    
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.6);
    }
    
    .menu-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.2);
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
    
    .menu-name {
        font-size: 1.3rem;
        font-weight: 900;
        flex: 1;
        line-height: 1.3;
    }
    
    .menu-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 1rem;
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
    
    .menu-image-placeholder {
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #999;
        font-size: 1rem;
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
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.2);
        margin-top: 0.5rem;
    }
    
    .menu-rating-small .score {
        font-size: 1rem;
    }
    
    .menu-rating-small .count {
        font-size: 0.75rem;
        opacity: 0.9;
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
        flex: 1;
    }
    
    .ingredient-item {
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .ingredient-item:last-child {
        border-bottom: none;
    }
    
    .comment-box {
        background: rgba(102, 126, 234, 0.08);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border-left: 4px solid #667eea;
    }
    
    .comment-author {
        color: #667eea;
        font-weight: bold;
        font-size: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    .board-post {
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s;
    }
    
    .board-post:hover {
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .menu-name {
            font-size: 1.1rem;
        }
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

        data = {
            "username": username,
            "password": password,
            "remember-me": "true"
        }

        response = requests.post(url, headers=login_headers, data=data)

        if response.status_code == 200:
            self.token = response.headers.get("Authorization")
            return True
        else:
            return False

    def get_menu(self, date=None, meal_type="2"):
        """메뉴 조회 (meal_type: 2=점심)"""
        if not self.token:
            raise Exception("Not logged in")

        url = f"{self.base_url}/api/meal"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})

        if date is None:
            date = datetime.now(KST)

        menu_dt = date.strftime("%Y%m%d")

        params = {
            "menuDt": menu_dt,
            "menuMealType": meal_type,
            "restaurantCode": "REST000595",
            "sortingFlag": "",
            "mainDivRestaurantCode": "REST000595",
            "activeRestaurantCode": "REST000595",
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            menu_data = response.json()
            return self._parse_menu(menu_data, menu_dt)
        else:
            return {"점심": [], "추가배식대": None}

    def get_menu_rating(self, menu_dt, hall_no, menu_course_type, 
                        menu_meal_type, restaurant_code):
        """메뉴 평점 조회"""
        if not self.token:
            return {"평균평점": 0, "참여자수": 0}

        url = f"{self.base_url}/api/meal/getMenuEvalAvg"
        headers = self.headers.copy()
        headers.update({"Authorization": self.token})

        params = {
            "menuDt": menu_dt,
            "hallNo": hall_no,
            "menuCourseType": menu_course_type,
            "menuMealType": menu_meal_type,
            "restaurantCode": restaurant_code,
            "mainDivRestaurantCode": restaurant_code,
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {
                    "평균평점": data.get("MENU_GRADE_AVG", 0),
                    "참여자수": data.get("TOT_CNT", 0),
                }
        except:
            pass

        return {"평균평점": 0, "참여자수": 0}

    def _parse_menu(self, menu_data, menu_dt):
        """메뉴 데이터 파싱 (추가 배식대 처리 포함)"""
        try:
            menu_items = []
            extra_station = None # 추가 배식대 정보 저장
            meal_list = menu_data.get("data", {}).get("mealList", [])

            # 전체 항목 중 '추가 배식대' 먼저 찾기
            for meal in meal_list:
                course_txt = meal.get("courseTxt", "")
                if "추가 배식대" in course_txt or "추가배식대" in course_txt:
                    extra_station = self._build_menu_info(meal, menu_dt)
                    break

            # 일반 메뉴 처리 (최대 4개 항목 처리, SELF 배식대 전까지)
            count = 0
            for meal in meal_list:
                if count >= 4:
                    break

                course_txt = meal.get("courseTxt", "")
                if course_txt == "SELF 배식대" or "추가 배식대" in course_txt or "추가배식대" in course_txt:
                    continue

                menu_info = self._build_menu_info(meal, menu_dt)
                menu_items.append(menu_info)
                count += 1

            # 라면 메뉴 추가
            for meal in meal_list:
                if meal.get("courseTxt", "") == "마이보글" or "[라면" in meal.get("menuName", ""):
                    menu_info = self._build_menu_info(meal, menu_dt)
                    menu_items.append(menu_info)
                    break

            return {"점심": menu_items, "추가배식대": extra_station}
        except Exception as e:
            st.error(f"메뉴 파싱 오류: {str(e)}")
            return {"점심": [], "추가배식대": None}

    def _build_menu_info(self, meal, menu_dt):
        """식단 객체 생성 공통 로직"""
        course_txt = meal.get("courseTxt", "")
        menu_name = meal.get("menuName", "")
        kcal = meal.get("sumKcal", "")
        sub_menu_txt = meal.get("subMenuTxt", "").split(",")

        photo_url = meal.get("photoUrl", "")
        photo_cd = meal.get("photoCd", "")
        image_url = f"{photo_url}{photo_cd}" if photo_url and photo_cd else None

        rating_info = self.get_menu_rating(
            meal.get("menuDt"),
            meal.get("hallNo"),
            meal.get("menuCourseType"),
            meal.get("menuMealType"),
            meal.get("restaurantCode"),
        )

        return {
            "코너": course_txt,
            "메뉴명": menu_name,
            "칼로리": kcal,
            "구성": sub_menu_txt,
            "이미지": image_url,
            "평균평점": rating_info["평균평점"],
            "참여자수": rating_info["참여자수"],
            "menu_id": f"{menu_dt}_{course_txt}_{menu_name}".replace(" ", "_"),
        }


# 데이터 저장/로드 함수들
def get_welstory_credentials():
    """웰스토리 계정 정보 가져오기 (Streamlit Secrets에서)"""
    try:
        if hasattr(st, 'secrets') and 'welstory' in st.secrets:
            return {
                'username': st.secrets['welstory']['username'],
                'password': st.secrets['welstory']['password']
            }
    except Exception as e:
        st.error(f"Secrets 로드 실패: {str(e)}")

    return {}

def load_votes():
    """투표 데이터 로드"""
    vote_file = DATA_DIR / "votes.json"
    if vote_file.exists():
        with open(vote_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_votes(votes):
    """투표 데이터 저장"""
    vote_file = DATA_DIR / "votes.json"
    with open(vote_file, 'w', encoding='utf-8') as f:
        json.dump(votes, f, ensure_ascii=False, indent=2)

def load_comments():
    """댓글 데이터 로드"""
    comment_file = DATA_DIR / "comments.json"
    if comment_file.exists():
        with open(comment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_comments(comments):
    """댓글 데이터 저장"""
    comment_file = DATA_DIR / "comments.json"
    with open(comment_file, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def load_board_posts():
    """게시판 글 로드"""
    board_file = DATA_DIR / "board.json"
    if board_file.exists():
        with open(board_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_board_posts(posts):
    """게시판 글 저장"""
    board_file = DATA_DIR / "board.json"
    with open(board_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def display_menu_card(menu_item, show_voting=True):
    """메뉴 카드 표시 (개선된 레이아웃)"""
    # st.markdown('<div class="menu-card">', unsafe_allow_html=True)

    # 메인 콘텐츠 영역
    st.markdown('<div class="menu-content">', unsafe_allow_html=True)

    # 이미지
    if menu_item.get("이미지"):
        st.markdown(f"""
        <div class="menu-image-container">
            <img src="{menu_item["이미지"]}" class="menu-image">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="menu-image-container">
            <div class="menu-image-placeholder">이미지 없음</div>
        </div>
        """, unsafe_allow_html=True)

    # 평점 (작게)
    if menu_item.get('평균평점', 0) > 0:
        st.markdown(f"""
        <div class="menu-rating-small">
            <span class="score">⭐ {menu_item['평균평점']:.1f}</span>
            <span class="count">({menu_item['참여자수']}명)</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="menu-rating-small">
            <span class="score">⭐</span>
            <span class="count">(평가 없음)</span>
        </div>
        """, unsafe_allow_html=True)

    # 칼로리
    st.markdown(f'<div class="menu-calories">🔥 {menu_item["칼로리"]}kcal</div>', unsafe_allow_html=True)

    # 구성 (한 줄씩)
    if menu_item['구성']:
        ingredients_html = '<div class="menu-ingredients">📋 <strong>구성</strong><br>'
        for ingredient in filter(None, menu_item['구성']):
            ingredients_html += f'<div class="ingredient-item">• {ingredient}</div>'
        ingredients_html += '</div>'
        st.markdown(ingredients_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # menu-content 종료

    # 투표 버튼
    if show_voting:
        votes = load_votes()
        menu_id = menu_item['menu_id']
        current_votes = votes.get(menu_id, {"좋아요": 0, "별로": 0})

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"👍 {current_votes['좋아요']}", key=f"like_{menu_id}", use_container_width=True):
                current_votes['좋아요'] += 1
                votes[menu_id] = current_votes
                save_votes(votes)
                st.rerun()

        with col2:
            if st.button(f"👎 {current_votes['별로']}", key=f"dislike_{menu_id}", use_container_width=True):
                current_votes['별로'] += 1
                votes[menu_id] = current_votes
                save_votes(votes)
                st.rerun()

    # 댓글 섹션
    with st.expander("💬 댓글 보기/작성"):
        comments = load_comments()
        menu_id = menu_item['menu_id']
        menu_comments = comments.get(menu_id, [])

        # 댓글 표시
        if menu_comments:
            for comment in menu_comments:
                st.markdown(f"""
                <div class="comment-box">
                    <div>
                        <span class="comment-author">{comment['author']}</span>
                        <span style="color: #999; font-size: 0.85rem;">· {comment['timestamp']}</span>
                    </div>
                    <div style="margin-top: 0.5rem;">{comment['text']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("첫 댓글을 남겨보세요!")

        # 댓글 작성
        with st.form(key=f"comment_{menu_id}"):
            col1, col2 = st.columns([1, 3])
            with col1:
                author = st.text_input("이름", key=f"author_{menu_id}", placeholder="익명")
            with col2:
                comment_text = st.text_input("댓글", key=f"text_{menu_id}", placeholder="이 메뉴 어떠셨나요?")

            submit = st.form_submit_button("작성", use_container_width=True)

            if submit and comment_text:
                if menu_id not in comments:
                    comments[menu_id] = []

                comments[menu_id].append({
                    "author": author if author else "익명",
                    "text": comment_text,
                    "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                })
                save_comments(comments)
                st.success("댓글이 작성되었습니다!")
                st.rerun()

    # st.markdown('</div>', unsafe_allow_html=True)  # menu-card 종료


def show_menu_page():
    """BOB SSAFY 메뉴 페이지"""
    # st.markdown('<p class="main-header">🍽️ BOB SSAFY 점심 메뉴</p>', unsafe_allow_html=True)

    # API 연결 확인
    if 'api' not in st.session_state or st.session_state.api is None:
        st.warning("⚠️ 웰스토리 API에 연결되지 않았습니다.")
        st.info("📝 `.streamlit/secrets.toml` 파일에 웰스토리 계정 정보를 설정하세요.")

        st.code("""[welstory]
username = "your_username"
password = "your_password"
""", language="toml")

        st.markdown("자세한 내용은 사이드바 하단의 '🔧 설정 필요'를 참고하세요.")
        return

    # 날짜 선택
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_date = st.date_input(
            "📅 날짜 선택",
            value=datetime.now(KST).date(),
            max_value=datetime.now(KST).date() + timedelta(days=7)
        )

    # 메뉴 로드
    try:
        with st.spinner("메뉴를 불러오는 중..."):
            menu_date = datetime.combine(selected_date, datetime.min.time())
            menu_date = KST.localize(menu_date)
            menu_data = st.session_state.api.get_menu(date=menu_date)

        if not menu_data.get("점심") and not menu_data.get("추가배식대"):
            st.warning("해당 날짜의 메뉴가 없습니다.")
            return

        # 일반 메뉴와 라면 메뉴 분리
        regular_menus = [m for m in menu_data["점심"] if "[라면" not in m.get("메뉴명", "")]
        ramen_menus = [m for m in menu_data["점심"] if "[라면" in m.get("메뉴명", "")]

        # 일반 메뉴 표시
        if regular_menus:
            st.markdown("### 🍱 메인 메뉴")

            # 메뉴 개수만큼 컬럼 생성 (최대 4개)
            num_cols = min(len(regular_menus), 4)
            
            # 메뉴 카드
            cols = st.columns(num_cols)
            for idx, menu in enumerate(regular_menus):
                with cols[idx % num_cols]:
                    # 컨테이너로 카드 생성
                    with st.container():
                        # 코너 + 메뉴명
                        st.markdown(f"""
                        <div style="
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            gap: 0.8rem;
                            margin-bottom: 1rem;
                            padding-bottom: 1rem;
                            border-bottom: 2px solid rgba(102, 126, 234, 0.2);
                        ">
                            <div class="menu-corner">{menu['코너']}</div>
                            <div style="
                                font-size: 1.2rem;
                                font-weight: 700;
                                line-height: 1.3;
                                text-align: center;
                                color: #667eea;
                            ">{menu['메뉴명']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 이미지
                        if menu.get("이미지"):
                            st.markdown(f"""
                            <div class="menu-image-container">
                                <img src="{menu["이미지"]}" class="menu-image">
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="menu-image-container">
                                <div class="menu-image-placeholder">이미지 없음</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 평점
                        if menu.get('평균평점', 0) > 0:
                            st.markdown(f"""
                            <div class="menu-rating-small">
                                <span class="score">⭐ {menu['평균평점']:.1f}</span>
                                <span class="count">({menu['참여자수']}명)</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="menu-rating-small">
                                <span class="score">⭐</span>
                                <span class="count">(평가 없음)</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 칼로리
                        st.markdown(f'<div class="menu-calories">🔥 {menu["칼로리"]}kcal</div>', unsafe_allow_html=True)
                        
                        # 구성
                        if menu['구성']:
                            ingredients_list = [ing for ing in menu['구성'] if ing]
                            ingredients_items = ''.join([f'<div class="ingredient-item">• {ing}</div>' for ing in ingredients_list])
                            st.markdown(f"""
                            <div class="menu-ingredients" style="min-height: 150px; max-height: 150px; overflow-y: auto;">
                                📋 <strong>구성</strong><br>
                                {ingredients_items}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="menu-ingredients" style="min-height: 150px; max-height: 150px;">
                                📋 <strong>구성</strong><br>
                                <div style="color: #999;">구성 정보 없음</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 카드 종료
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 투표 버튼
                    votes = load_votes()
                    menu_id = menu['menu_id']
                    current_votes = votes.get(menu_id, {"좋아요": 0, "별로": 0})
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"👍 {current_votes['좋아요']}", key=f"like_{menu_id}", use_container_width=True):
                            current_votes['좋아요'] += 1
                            votes[menu_id] = current_votes
                            save_votes(votes)
                            st.rerun()
                    
                    with col2:
                        if st.button(f"👎 {current_votes['별로']}", key=f"dislike_{menu_id}", use_container_width=True):
                            current_votes['별로'] += 1
                            votes[menu_id] = current_votes
                            save_votes(votes)
                            st.rerun()
                    
                    # 댓글 섹션
                    with st.expander("💬 댓글
