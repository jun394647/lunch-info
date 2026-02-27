import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from pathlib import Path

# ... (기존 hide_streamlit_style 및 CSS 스타일링 유지) ...
# CSS 스타일링 부분에 추가 배식대용 스타일을 살짝 추가했습니다.
st.markdown("""
    <style>
    /* 기존 스타일 유지 */
    .extra-station-card {
        background: rgba(102, 126, 234, 0.05);
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    /* ... 나머지 기존 스타일 동일 ... */
    </style>
""", unsafe_allow_html=True)

class WelplusAPI:
    # ... (init, login 등 기존 메서드 유지) ...

    def _parse_menu(self, menu_data, menu_dt):
        """메뉴 데이터 파싱 - 추가 배식대 로직 추가"""
        try:
            menu_items = []
            extra_station = None  # 추가 배식대 저장용
            meal_list = menu_data.get("data", {}).get("mealList", [])

            for meal in meal_list:
                course_txt = meal.get("courseTxt", "")
                menu_name = meal.get("menuName", "")
                
                # 데이터 추출 공통 로직
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

                # 1. 추가 배식대인 경우 별도로 저장
                if "추가 배식대" in course_txt or "추가배식대" in course_txt:
                    extra_station = menu_info
                    continue # 일반 리스트에는 넣지 않음

                # 2. 일반 메뉴 처리 (최대 4개 및 SELF 배식대 전까지 - 기존 로직 유지)
                if len([m for m in menu_items if "[라면" not in m["메뉴명"]]) < 4:
                    if course_txt != "SELF 배식대" and "마이보글" not in course_txt and "[라면" not in menu_name:
                        menu_items.append(menu_info)
                
                # 3. 라면 메뉴 처리 (기존 로직 유지)
                if ("마이보글" in course_txt or "[라면" in menu_name) and not any("[라면" in m["메뉴명"] for m in menu_items):
                    menu_items.append(menu_info)

            return {"점심": menu_items, "추가배식대": extra_station}
        except Exception as e:
            st.error(f"메뉴 파싱 오류: {str(e)}")
            return {"점심": [], "추가배식대": None}

# ... (데이터 저장/로드 및 display_menu_card 유지) ...

def show_menu_page():
    """BOB SSAFY 메뉴 페이지 (추가 배식대 기능 포함)"""
    # ... (날짜 선택 및 API 로드 로직 기존과 동일) ...
    try:
        with st.spinner("메뉴를 불러오는 중..."):
            menu_date = datetime.combine(selected_date, datetime.min.time())
            menu_date = KST.localize(menu_date)
            menu_data = st.session_state.api.get_menu(date=menu_date)

        if not menu_data.get("점심") and not menu_data.get("추가배식대"):
            st.warning("해당 날짜의 메뉴가 없습니다.")
            return

        # --- [1] 메인 메뉴 & 라면 메뉴 표시 (기존 코드 유지) ---
        regular_menus = [m for m in menu_data["점심"] if "[라면" not in m.get("메뉴명", "")]
        ramen_menus = [m for m in menu_data["점심"] if "[라면" in m.get("메뉴명", "")]

        if regular_menus:
            st.markdown("### 🍱 메인 메뉴")
            num_cols = min(len(regular_menus), 4)
            cols = st.columns(num_cols)
            for idx, menu in enumerate(regular_menus):
                with cols[idx % num_cols]:
                    # (기존의 복잡한 카드 렌더링 코드 유지...)
                    with st.container():
                        st.markdown(f"""
                        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.8rem; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 2px solid rgba(102, 126, 234, 0.2);">
                            <div class="menu-corner">{menu['코너']}</div>
                            <div style="font-size: 1.2rem; font-weight: 700; line-height: 1.3; text-align: center; color: #667eea;">{menu['메뉴명']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if menu.get("이미지"):
                            st.markdown(f'<div class="menu-image-container"><img src="{menu["이미지"]}" class="menu-image"></div>', unsafe_allow_html=True)
                        # ... (평점, 칼로리, 구성 등 기존 코드 모두 동일하게 유지) ...
                        st.markdown(f'<div class="menu-calories">🔥 {menu["칼로리"]}kcal</div>', unsafe_allow_html=True)
                        if menu['구성']:
                            ingredients_items = ''.join([f'<div class="ingredient-item">• {ing}</div>' for ing in menu['구성'] if ing])
                            st.markdown(f'<div class="menu-ingredients" style="min-height: 150px; max-height: 150px; overflow-y: auto;">📋 <strong>구성</strong><br>{ingredients_items}</div>', unsafe_allow_html=True)
                    
                    # 투표/댓글 로직 생략 (기존 코드 그대로 두시면 됩니다)

        if ramen_menus:
            st.markdown("---")
            st.markdown("### 🍜 라면 메뉴")
            for menu in ramen_menus:
                # (기존 라면 렌더링 코드 유지...)
                st.markdown(f'<div class="menu-header"><div class="menu-corner">{menu["코너"]}</div><div class="menu-name">{menu["메뉴명"]}</div></div>', unsafe_allow_html=True)
                # ... (라면 상세 내용 코드 유지)

        # --- [2] 추가 배식대 표시 (페이지 맨 밑에 추가) ---
        extra = menu_data.get("추가배식대")
        if extra:
            st.markdown("---")
            st.markdown("### ➕ 오늘 품절 시 추가 배식대")
            
            with st.container():
                # 디자인 일관성을 위해 기존 스타일을 차용하되 구분되도록 구성
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if extra.get("이미지"):
                        st.markdown(f'<div class="menu-image-container" style="height: 180px;"><img src="{extra["이미지"]}" class="menu-image"></div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="menu-image-container" style="height: 180px;"><div class="menu-image-placeholder">이미지 없음</div></div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div style="padding: 10px;">
                            <span class="menu-corner" style="background: #FF6B35; margin-bottom: 10px;">{extra['코너']}</span>
                            <h4 style="margin: 10px 0;">{extra['메뉴명']}</h4>
                            <p style="color: #667eea; font-weight: bold;">🔥 {extra['칼로리']}kcal</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if extra['구성']:
                        items = "".join([f"<span>{ing} </span>" for ing in extra['구성'] if ing])
                        st.info(f"📋 구성: {items}")

    except Exception as e:
        st.error(f"메뉴 로드 중 오류 발생: {str(e)}")

# ... (나머지 main 함수 등 유지) ...
