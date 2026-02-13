import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="웰스토리 메뉴 보드",
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
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1.5rem;
        color: #FF6B6B;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .menu-card {
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
    }
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .menu-image {
        border-radius: 10px;
        margin-bottom: 0.8rem;
        width: 100%;
        object-fit: cover;
        height: 200px;
    }
    .menu-corner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .menu-name {
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 0.5rem 0;
    }
    .menu-detail {
        font-size: 0.85rem;
        color: #666;
        margin: 0.3rem 0;
    }
    .rating-section {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFE8CC 100%);
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.8rem 0;
        text-align: center;
    }
    .vote-section {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 10px;
        margin-top: 0.8rem;
    }
    .comment-box {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .board-post {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0;
        transition: box-shadow 0.2s;
    }
    .board-post:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    /* 버튼 스타일 개선 */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    /* 날짜 선택기 스타일 */
    .stDateInput>div>div>input {
        border-radius: 8px;
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
            return {"점심": []}

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
        """메뉴 데이터 파싱"""
        try:
            menu_items = []
            meal_list = menu_data.get("data", {}).get("mealList", [])
            
            # 최대 4개 항목 처리 (SELF 배식대 전까지)
            count = 0
            for meal in meal_list:
                if count >= 4:
                    break
                
                course_txt = meal.get("courseTxt", "")
                if course_txt == "SELF 배식대":
                    break
                
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
                
                menu_info = {
                    "코너": course_txt,
                    "메뉴명": menu_name,
                    "칼로리": kcal,
                    "구성": sub_menu_txt,
                    "이미지": image_url,
                    "평균평점": rating_info["평균평점"],
                    "참여자수": rating_info["참여자수"],
                    "menu_id": f"{menu_dt}_{course_txt}_{menu_name}".replace(" ", "_"),
                }
                menu_items.append(menu_info)
                count += 1
            
            # 라면 메뉴 추가
            for meal in meal_list:
                if meal.get("courseTxt", "") == "마이보글" or "[라면" in meal.get("menuName", ""):
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
                    
                    menu_info = {
                        "코너": course_txt,
                        "메뉴명": menu_name,
                        "칼로리": kcal,
                        "구성": sub_menu_txt,
                        "이미지": image_url,
                        "평균평점": rating_info["평균평점"],
                        "참여자수": rating_info["참여자수"],
                        "menu_id": f"{menu_dt}_{course_txt}_{menu_name}".replace(" ", "_"),
                    }
                    menu_items.append(menu_info)
                    break
            
            return {"점심": menu_items}
        except Exception as e:
            st.error(f"메뉴 파싱 오류: {str(e)}")
            return {"점심": []}


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
    """메뉴 카드 표시 (컴팩트 버전)"""
    with st.container():
        # 이미지
        if menu_item.get("이미지"):
            st.markdown(f'<img src="{menu_item["이미지"]}" class="menu-image">', unsafe_allow_html=True)
        else:
            st.markdown('<div style="height: 200px; background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #999;">이미지 없음</div>', unsafe_allow_html=True)
        
        # 코너 태그
        st.markdown(f'<div class="menu-corner">{menu_item["코너"]}</div>', unsafe_allow_html=True)
        
        # 메뉴명
        st.markdown(f'<div class="menu-name">{menu_item["메뉴명"]}</div>', unsafe_allow_html=True)
        
        # 칼로리
        st.markdown(f'<div class="menu-detail">🔥 {menu_item["칼로리"]}kcal</div>', unsafe_allow_html=True)
        
        # 구성 (간략하게)
        if menu_item['구성']:
            ingredients = ", ".join(filter(None, menu_item['구성'][:3]))  # 최대 3개만
            if len(menu_item['구성']) > 3:
                ingredients += "..."
            st.markdown(f'<div class="menu-detail" style="font-size: 0.75rem; color: #888;">{ingredients}</div>', unsafe_allow_html=True)
        
        # 평점
        if menu_item.get('평균평점', 0) > 0:
            st.markdown(f"""
            <div class="rating-section">
                <div style="font-size: 1.3rem;">⭐ {menu_item['평균평점']:.1f}</div>
                <div style="font-size: 0.75rem; color: #666; margin-top: 0.2rem;">{menu_item['참여자수']}명 참여</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="rating-section"><div style="font-size: 0.85rem; color: #999;">평가 없음</div></div>', unsafe_allow_html=True)
        
        # 투표 기능
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
        
        # 댓글 섹션 (expander로)
        with st.expander("💬 댓글", expanded=False):
            comments = load_comments()
            menu_id = menu_item['menu_id']
            menu_comments = comments.get(menu_id, [])
            
            # 댓글 표시
            if menu_comments:
                for comment in menu_comments[-3:]:  # 최근 3개만
                    st.markdown(f"""
                    <div class="comment-box">
                        <strong style="color: #667eea;">{comment['author']}</strong>
                        <span style="font-size: 0.7rem; color: #999;"> · {comment['timestamp'].split()[1]}</span><br>
                        <span style="font-size: 0.85rem;">{comment['text']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                if len(menu_comments) > 3:
                    st.caption(f"외 {len(menu_comments) - 3}개 댓글")
            
            # 댓글 작성
            with st.form(key=f"comment_{menu_id}"):
                author = st.text_input("이름", key=f"author_{menu_id}", placeholder="익명")
                comment_text = st.text_area("댓글", key=f"text_{menu_id}", placeholder="이 메뉴 어떠셨나요?", max_chars=200)
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


def show_menu_page():
    """메뉴 페이지"""
    st.markdown('<p class="main-header">🍽️ 오늘의 점심 메뉴</p>', unsafe_allow_html=True)
    
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
        
        if not menu_data.get("점심"):
            st.warning("해당 날짜의 메뉴가 없습니다.")
            return
        
        # 일반 메뉴와 라면 메뉴 분리
        regular_menus = [m for m in menu_data["점심"] if "[라면" not in m.get("메뉴명", "")]
        ramen_menus = [m for m in menu_data["점심"] if "[라면" in m.get("메뉴명", "")]
        
        # 일반 메뉴 3열 레이아웃
        if regular_menus:
            st.markdown("### 🍱 메인 메뉴")
            
            # 3개씩 나눠서 표시
            for i in range(0, len(regular_menus), 3):
                cols = st.columns(3)
                for idx, menu in enumerate(regular_menus[i:i+3]):
                    with cols[idx]:
                        st.markdown('<div class="menu-card">', unsafe_allow_html=True)
                        display_menu_card(menu)
                        st.markdown('</div>', unsafe_allow_html=True)
        
        # 라면 메뉴 (2열로 크게)
        if ramen_menus:
            st.markdown("---")
            st.markdown("### 🍜 라면 메뉴")
            
            for menu in ramen_menus:
                # 라면 종류와 토핑 분리
                ramen_types = []
                toppings = []
                topping_idx = -1
                
                for i, item in enumerate(menu.get("구성", [])):
                    if "[토핑" in item:
                        topping_idx = i
                        break
                
                if topping_idx > 0:
                    ramen_types = menu["구성"][1:topping_idx]
                    toppings = menu["구성"][topping_idx+1:]
                else:
                    ramen_types = menu["구성"][1:] if len(menu["구성"]) > 1 else []
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if menu.get("이미지"):
                        st.image(menu["이미지"], use_container_width=True)
                    else:
                        st.info("이미지 없음")
                
                with col2:
                    st.markdown(f'<div class="menu-corner">{menu["코너"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="menu-name">{menu["메뉴명"]}</div>', unsafe_allow_html=True)
                    
                    if ramen_types:
                        st.markdown("**🍜 라면 종류:**")
                        st.write(", ".join(ramen_types))
                    
                    if toppings:
                        st.markdown("**🥚 토핑:**")
                        st.write(", ".join(toppings))
    
    except Exception as e:
        st.error(f"메뉴 로드 중 오류 발생: {str(e)}")


def show_board_page():
    """게시판 페이지"""
    st.markdown('<p class="main-header">📋 자유 게시판</p>', unsafe_allow_html=True)
    
    posts = load_board_posts()
    
    # 글쓰기 버튼
    col1, col2 = st.columns([3, 1])
    with col2:
        write_mode = st.button("✍️ 새 글 작성", use_container_width=True, type="primary")
    
    # 글쓰기 모드
    if write_mode or 'writing' in st.session_state and st.session_state.writing:
        st.session_state.writing = True
        
        with st.form("new_post", clear_on_submit=True):
            st.markdown("### ✍️ 새 글 작성")
            title = st.text_input("제목", placeholder="제목을 입력하세요")
            author = st.text_input("작성자", placeholder="익명")
            content = st.text_area("내용", height=200, placeholder="내용을 입력하세요")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                submit = st.form_submit_button("작성", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("취소", use_container_width=True)
            
            if cancel:
                st.session_state.writing = False
                st.rerun()
            
            if submit and title and content:
                new_post = {
                    "id": len(posts),
                    "title": title,
                    "author": author if author else "익명",
                    "content": content,
                    "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
                    "comments": []
                }
                posts.insert(0, new_post)
                save_board_posts(posts)
                st.session_state.writing = False
                st.success("게시글이 작성되었습니다!")
                st.rerun()
    
    # 게시글 목록
    st.markdown("---")
    if not posts:
        st.info("아직 작성된 글이 없습니다. 첫 글을 작성해보세요!")
    else:
        for post in posts:
            with st.expander(f"**{post['title']}** · {post['author']} · {post['timestamp']}", expanded=False):
                st.markdown(f'<div class="board-post">{post["content"]}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 💬 댓글")
                
                # 댓글 표시
                if post.get('comments'):
                    for comment in post['comments']:
                        st.markdown(f"""
                        <div class="comment-box">
                            <strong style="color: #667eea;">{comment['author']}</strong>
                            <span style="font-size: 0.75rem; color: #999;"> · {comment['timestamp']}</span><br>
                            <span style="font-size: 0.9rem;">{comment['text']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("첫 댓글을 남겨보세요!")
                
                # 댓글 작성
                with st.form(f"comment_post_{post['id']}"):
                    c_col1, c_col2 = st.columns([1, 4])
                    with c_col1:
                        c_author = st.text_input("이름", key=f"c_author_{post['id']}", placeholder="익명")
                    with c_col2:
                        c_text = st.text_input("댓글", key=f"c_text_{post['id']}", placeholder="댓글을 입력하세요")
                    
                    c_submit = st.form_submit_button("댓글 작성", use_container_width=True)
                    
                    if c_submit and c_text:
                        if 'comments' not in post:
                            post['comments'] = []
                        
                        post['comments'].append({
                            "author": c_author if c_author else "익명",
                            "text": c_text,
                            "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                        })
                        save_board_posts(posts)
                        st.success("댓글이 작성되었습니다!")
                        st.rerun()


def show_stats_page():
    """통계 페이지"""
    st.markdown('<p class="main-header">📊 메뉴 통계</p>', unsafe_allow_html=True)
    
    votes = load_votes()
    
    if not votes:
        st.info("아직 투표 데이터가 없습니다.")
        return
    
    # 전체 통계 카드
    total_likes = sum(v['좋아요'] for v in votes.values())
    total_dislikes = sum(v['별로'] for v in votes.values())
    total_votes = total_likes + total_dislikes
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👍</div>
            <div style="font-size: 2.5rem; font-weight: bold;">{total_likes}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 0.3rem;">총 좋아요</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👎</div>
            <div style="font-size: 2.5rem; font-weight: bold;">{total_dislikes}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 0.3rem;">총 별로</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <div style="font-size: 2.5rem; font-weight: bold;">{total_votes}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 0.3rem;">총 투표수</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 인기 메뉴 TOP 5
    st.markdown("### 🏆 인기 메뉴 TOP 5")
    
    menu_scores = []
    for menu_id, vote_data in votes.items():
        total = vote_data['좋아요'] + vote_data['별로']
        if total > 0:
            score = vote_data['좋아요'] / total * 100
            menu_scores.append({
                "메뉴": menu_id.split('_')[-1] if '_' in menu_id else menu_id,
                "좋아요": vote_data['좋아요'],
                "별로": vote_data['별로'],
                "좋아요율": score,
                "총투표": total
            })
    
    menu_scores.sort(key=lambda x: x['좋아요율'], reverse=True)
    
    if menu_scores:
        for idx, menu in enumerate(menu_scores[:5], 1):
            # 메달 이모지
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            
            # 진행 바 생성
            progress_html = f"""
            <div style="background: white; border-radius: 10px; padding: 1rem; margin: 0.8rem 0; border: 1px solid #e0e0e0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <span style="font-size: 1.3rem; margin-right: 0.5rem;">{medal}</span>
                        <strong style="font-size: 1.1rem;">{menu['메뉴']}</strong>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.2rem; font-weight: bold; color: #667eea;">{menu['좋아요율']:.1f}%</span>
                    </div>
                </div>
                <div style="background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {menu['좋아요율']:.1f}%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.85rem; color: #666;">
                    <span>👍 {menu['좋아요']} · 👎 {menu['별로']}</span>
                    <span>총 {menu['총투표']}표</span>
                </div>
            </div>
            """
            st.markdown(progress_html, unsafe_allow_html=True)
    else:
        st.info("투표 데이터가 없습니다.")


def main():
    # 계정 정보 가져오기 (Streamlit Secrets에서)
    credentials = get_welstory_credentials()
    
    # 세션 상태 초기화
    if 'api' not in st.session_state:
        st.session_state.api = None
        st.session_state.logged_in = False
    
    # 자동 로그인 (페이지 로드 시 한 번만)
    if not st.session_state.logged_in and credentials.get('username') and credentials.get('password'):
        try:
            with st.spinner("메뉴 정보를 불러오는 중..."):
                api = WelplusAPI()
                if api.login(credentials['username'], credentials['password']):
                    st.session_state.api = api
                    st.session_state.logged_in = True
        except Exception as e:
            st.error(f"API 연결 실패: {str(e)}")
    
    # 사이드바
    with st.sidebar:
        st.markdown("## 🍽️ 웰스토리 메뉴 보드")
        st.markdown("---")
        
        # 메뉴 선택
        page = st.radio(
            "페이지 선택",
            ["🍽️ 오늘의 메뉴", "📋 자유 게시판", "📊 통계"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # API 연결 상태 (하단에 간단하게 표시)
        if st.session_state.logged_in:
            st.success("✅ 연결됨")
        else:
            st.error("❌ 연결 안됨")
            with st.expander("🔧 설정 필요"):
                st.markdown("""
                **Streamlit Secrets 설정:**
                
                `.streamlit/secrets.toml` 파일에 계정 정보를 추가하세요:
                
                ```toml
                [welstory]
                username = "your_username"
                password = "your_password"
                ```
                """)
    
    # 메인 페이지
    if page == "🍽️ 오늘의 메뉴":
        show_menu_page()
    elif page == "📋 자유 게시판":
        show_board_page()
    elif page == "📊 통계":
        show_stats_page()


if __name__ == "__main__":
    main()
