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
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #FF6B6B;
    }
    .menu-card {
        border: 2px solid #f0f0f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .rating-section {
        background-color: #FFF9E6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .comment-box {
        background-color: #F5F5F5;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
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
    """메뉴 카드 표시"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if menu_item.get("이미지"):
            st.image(menu_item["이미지"], use_container_width=True)
        else:
            st.info("이미지 없음")
    
    with col2:
        st.markdown(f"### {menu_item['코너']}")
        st.markdown(f"**{menu_item['메뉴명']}**")
        st.markdown(f"📊 칼로리: {menu_item['칼로리']}kcal")
        
        if menu_item['구성']:
            st.markdown("**구성:**")
            st.markdown(", ".join(filter(None, menu_item['구성'])))
        
        # 평점 표시
        if menu_item.get('평균평점', 0) > 0:
            st.markdown(f"⭐ **평점:** {menu_item['평균평점']:.1f} ({menu_item['참여자수']}명 참여)")
        else:
            st.markdown("⭐ **평점:** 평가 없음")
    
    # 투표 기능
    if show_voting:
        st.markdown("---")
        votes = load_votes()
        menu_id = menu_item['menu_id']
        current_votes = votes.get(menu_id, {"좋아요": 0, "별로": 0})
        
        col_vote1, col_vote2, col_vote3 = st.columns([1, 1, 2])
        
        with col_vote1:
            if st.button(f"👍 좋아요 ({current_votes['좋아요']})", key=f"like_{menu_id}"):
                current_votes['좋아요'] += 1
                votes[menu_id] = current_votes
                save_votes(votes)
                st.rerun()
        
        with col_vote2:
            if st.button(f"👎 별로 ({current_votes['별로']})", key=f"dislike_{menu_id}"):
                current_votes['별로'] += 1
                votes[menu_id] = current_votes
                save_votes(votes)
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
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_date = st.date_input(
            "날짜 선택",
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
        
        # 일반 메뉴 표시
        st.markdown("### 🍱 메인 메뉴")
        regular_menus = [m for m in menu_data["점심"] if "[라면" not in m.get("메뉴명", "")]
        
        for menu in regular_menus:
            with st.container():
                st.markdown('<div class="menu-card">', unsafe_allow_html=True)
                display_menu_card(menu)
                
                # 댓글 섹션
                with st.expander("💬 댓글 보기/작성"):
                    comments = load_comments()
                    menu_id = menu['menu_id']
                    menu_comments = comments.get(menu_id, [])
                    
                    # 댓글 표시
                    if menu_comments:
                        for idx, comment in enumerate(menu_comments):
                            st.markdown(f"""
                            <div class="comment-box">
                                <strong>{comment['author']}</strong> - {comment['timestamp']}<br>
                                {comment['text']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("첫 댓글을 남겨보세요!")
                    
                    # 댓글 작성
                    with st.form(key=f"comment_{menu_id}"):
                        author = st.text_input("이름", key=f"author_{menu_id}")
                        comment_text = st.text_area("댓글", key=f"text_{menu_id}")
                        submit = st.form_submit_button("댓글 작성")
                        
                        if submit and author and comment_text:
                            if menu_id not in comments:
                                comments[menu_id] = []
                            
                            comments[menu_id].append({
                                "author": author,
                                "text": comment_text,
                                "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                            })
                            save_comments(comments)
                            st.success("댓글이 작성되었습니다!")
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
        
        # 라면 메뉴 표시
        ramen_menus = [m for m in menu_data["점심"] if "[라면" in m.get("메뉴명", "")]
        if ramen_menus:
            st.markdown("### 🍜 라면 메뉴")
            for menu in ramen_menus:
                with st.container():
                    st.markdown('<div class="menu-card">', unsafe_allow_html=True)
                    
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
                        ramen_types = menu["구성"][1:]
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if menu.get("이미지"):
                            st.image(menu["이미지"], use_container_width=True)
                    
                    with col2:
                        st.markdown(f"### {menu['코너']}")
                        st.markdown(f"**{menu['메뉴명']}**")
                        
                        if ramen_types:
                            st.markdown("**라면 종류:**")
                            st.markdown(", ".join(ramen_types))
                        
                        if toppings:
                            st.markdown("**토핑:**")
                            st.markdown(", ".join(toppings))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"메뉴 로드 중 오류 발생: {str(e)}")


def show_board_page():
    """게시판 페이지"""
    st.markdown('<p class="main-header">📋 자유 게시판</p>', unsafe_allow_html=True)
    
    posts = load_board_posts()
    
    # 글쓰기 섹션
    with st.expander("✍️ 새 글 작성", expanded=False):
        with st.form("new_post"):
            title = st.text_input("제목")
            author = st.text_input("작성자")
            content = st.text_area("내용", height=200)
            submit = st.form_submit_button("작성하기")
            
            if submit and title and author and content:
                new_post = {
                    "id": len(posts),
                    "title": title,
                    "author": author,
                    "content": content,
                    "timestamp": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
                    "comments": []
                }
                posts.insert(0, new_post)
                save_board_posts(posts)
                st.success("게시글이 작성되었습니다!")
                st.rerun()
    
    # 게시글 목록
    st.markdown("---")
    if not posts:
        st.info("아직 작성된 글이 없습니다. 첫 글을 작성해보세요!")
    else:
        for post in posts:
            with st.expander(f"**{post['title']}** - {post['author']} ({post['timestamp']})"):
                st.markdown(post['content'])
                
                st.markdown("---")
                st.markdown("**💬 댓글**")
                
                # 댓글 표시
                if post.get('comments'):
                    for comment in post['comments']:
                        st.markdown(f"""
                        <div class="comment-box">
                            <strong>{comment['author']}</strong> - {comment['timestamp']}<br>
                            {comment['text']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # 댓글 작성
                with st.form(f"comment_post_{post['id']}"):
                    c_author = st.text_input("이름", key=f"c_author_{post['id']}")
                    c_text = st.text_area("댓글", key=f"c_text_{post['id']}")
                    c_submit = st.form_submit_button("댓글 작성")
                    
                    if c_submit and c_author and c_text:
                        if 'comments' not in post:
                            post['comments'] = []
                        
                        post['comments'].append({
                            "author": c_author,
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
    
    # 투표 데이터 분석
    st.markdown("### 👍 인기 메뉴 TOP 5")
    
    menu_scores = []
    for menu_id, vote_data in votes.items():
        total = vote_data['좋아요'] + vote_data['별로']
        if total > 0:
            score = vote_data['좋아요'] / total * 100
            menu_scores.append({
                "메뉴": menu_id.split('_')[-1] if '_' in menu_id else menu_id,
                "좋아요": vote_data['좋아요'],
                "별로": vote_data['별로'],
                "좋아요율": score
            })
    
    menu_scores.sort(key=lambda x: x['좋아요율'], reverse=True)
    
    if menu_scores:
        for idx, menu in enumerate(menu_scores[:5], 1):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{idx}. {menu['메뉴']}**")
            with col2:
                st.markdown(f"👍 {menu['좋아요']} 👎 {menu['별로']}")
            with col3:
                st.markdown(f"**{menu['좋아요율']:.1f}%**")
    
    st.markdown("---")
    
    # 전체 투표 현황
    st.markdown("### 📈 전체 투표 현황")
    total_likes = sum(v['좋아요'] for v in votes.values())
    total_dislikes = sum(v['별로'] for v in votes.values())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("총 좋아요", total_likes)
    with col2:
        st.metric("총 별로", total_dislikes)


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
