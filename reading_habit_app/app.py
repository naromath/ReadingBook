import streamlit as st
import requests
import base64

# --- 🔐 인증 기능 추가 ---
def check_password():
    """로그인 성공 시 True를 반환합니다."""
    def password_entered():
        # 유저님이 정한 비밀번호를 'your_password' 자리에 입력하세요.
        if st.session_state["password"] == "615015!!": # <- 여기에 비밀번호 설정
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 보안을 위해 세션에서 비밀번호 삭제
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 로그인 화면 UI
        st.text_input("접근 권한이 필요합니다. 비밀번호를 입력하세요.", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("비밀번호가 틀렸습니다. 다시 입력하세요.", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

# 인증 통과 시에만 아래 메인 코드를 실행
if not check_password():
    st.stop()

API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="나만의 AI 독서 비서", page_icon="📚", layout="centered")

if "book_data" not in st.session_state:
    st.session_state.book_data = None
if "curation_data" not in st.session_state:
    st.session_state.curation_data = None
if "user_goal" not in st.session_state:
    st.session_state.user_goal = ""
if "detected_title" not in st.session_state:
    st.session_state.detected_title = ""

# DB에서 과거 기록을 가져오는 함수
def load_reading_logs(book_title):
    try:
        res = requests.get(f"{API_BASE_URL}/logs/{book_title}")
        if res.status_code == 200 and res.json().get("status") == "success":
            return res.json()["data"]
        return []
    except:
        return []

# 📝 (NEW!) 옵시디언(Second Brain) 친화적인 마크다운 생성 함수
def generate_markdown(book, curation, logs, goal):
    # YAML Frontmatter (옵시디언 등의 속성값으로 자동 인식됨)
    md = "---\n"
    md += f"title: {book['title']}\n"
    md += f"author: {', '.join(book['authors'])}\n"
    md += f"total_pages: {book['page_count']}\n"
    md += "tags: [독서노트, Second_Brain]\n"
    md += "---\n\n"
    
    # 본문 시작
    md += f"# 📚 {book['title']}\n\n"
    if book['thumbnail']:
        md += f"![Cover]({book['thumbnail']})\n\n"
        
    md += "## 🎯 나의 목표 및 AI 큐레이션\n"
    md += f"- **나의 목표**: {goal}\n"
    md += f"- **AI 추천사**: {curation['curation_message']}\n"
    md += f"- **독서 팁**: {curation['schedule_advice']}\n\n"
    
    md += "---\n\n"
    md += "## ✍️ 데일리 독서 기록\n\n"
    
    # 기록을 과거부터 순서대로 읽기 위해 역순(시간순)으로 뒤집어 줍니다.
    chronological_logs = reversed(logs)
    
    for log in chronological_logs:
        date_str = log['created_at'][:10] # YYYY-MM-DD 포맷
        md += f"### 📅 {date_str} (p. {log['read_pages']})\n\n"
        md += f"**나의 감상:**\n> {log['user_thought']}\n\n"
        md += f"**🤖 AI 페이스메이커:**\n> {log['ai_feedback']}\n\n"
    
    return md

st.title("📚 나만의 AI 독서 비서")
st.subheader("책을 스캔하고 1주일 맞춤형 독서 계획을 받아보세요!")

st.markdown("---")

# --- 📷 카메라 촬영으로 책 등록 ---
st.subheader("📷 책 표지 촬영으로 자동 등록")
st.caption("카메라로 책 표지를 찍으면 AI가 제목을 자동으로 인식합니다.")
img_file = st.camera_input("책 표지가 잘 보이도록 촬영해 주세요")

if img_file:
    bytes_data = img_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{base64_image}"

    with st.spinner("🤖 AI가 책을 확인하고 있습니다..."):
        try:
            res = requests.post(f"{API_BASE_URL}/analyze-cover", json={"image": data_url})
            if res.status_code == 200:
                book_info = res.json()["data"]
                st.session_state.detected_title = book_info.get('title', '')
                st.success(f"📖 찾았습니다! **제목:** {book_info.get('title', '알 수 없음')} / **저자:** {book_info.get('author', '알 수 없음')}")
                st.info("아래 검색창에 인식된 제목이 자동으로 입력되었습니다. 목표를 입력하고 검색 버튼을 눌러주세요.")
            else:
                st.error("책을 인식하지 못했습니다. 다시 촬영해 주세요.")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

st.markdown("---")

# --- 🔍 ISBN / 제목 검색 섹션 ---
col1, col2 = st.columns(2)
with col1:
    isbn_input = st.text_input("1️⃣ 책 제목 또는 ISBN 입력", value=st.session_state.detected_title, placeholder="예: 9791190538510")
with col2:
    goal_input = st.text_input("2️⃣ 이번 주 독서 목표는?", placeholder="예: 마흔을 앞두고 내면의 성장")

if st.button("검색 및 AI 큐레이션 시작 🚀", use_container_width=True):
    if not isbn_input or not goal_input:
        st.warning("ISBN과 독서 목표를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("책 정보와 AI 큐레이션을 가져오는 중입니다..."):
                book_res = requests.get(f"{API_BASE_URL}/books/{isbn_input}")
                book_res.raise_for_status()
                b_data = book_res.json()
                
                if b_data.get("status") == "success":
                    st.session_state.book_data = b_data["data"]
                    st.session_state.user_goal = goal_input
                    
                    curation_payload = {
                        "user_goal": goal_input,
                        "book_title": st.session_state.book_data["title"],
                        "total_pages": st.session_state.book_data["page_count"]
                    }
                    cur_res = requests.post(f"{API_BASE_URL}/curation", json=curation_payload)
                    cur_res.raise_for_status()
                    c_data = cur_res.json()
                    
                    if c_data.get("status") == "success":
                        st.session_state.curation_data = c_data["data"]
                    else:
                        st.error("AI 큐레이션을 가져오는데 실패했습니다.")
                else:
                    st.error(b_data.get("message", "책 정보를 찾을 수 없습니다."))
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# 화면 출력부
if st.session_state.book_data and st.session_state.curation_data:
    book = st.session_state.book_data
    curation = st.session_state.curation_data
    
    b_col1, b_col2 = st.columns([1, 2])
    with b_col1:
        if book["thumbnail"]:
            st.image(book["thumbnail"], width=150)
    with b_col2:
        st.write(f"**제목:** {book['title']}")
        st.write(f"**저자:** {', '.join(book['authors'])}")
        st.write(f"**총 페이지 수:** {book['page_count']}쪽")
    
    st.markdown("---")
    
    st.subheader("✨ AI 큐레이션 결과")
    st.info(f"💡 **AI의 추천사:**\n{curation['curation_message']}")
    st.metric(label="하루 권장 독서량", value=f"{curation['daily_pages']} 쪽", delta="1주일 완독 페이스")
    
    st.markdown("---")
    
    st.subheader("📝 데일리 독서 기록")
    log_col1, log_col2 = st.columns([1, 2])
    with log_col1:
        read_pages = st.number_input("오늘 누적 읽은 쪽수", min_value=1, max_value=book["page_count"], value=curation['daily_pages'])
    with log_col2:
        user_thought = st.text_area("오늘 읽은 부분에서 인상 깊었던 점은?")
        
    if st.button("기록 저장 및 AI 피드백 받기 💌"):
        if not user_thought:
            st.warning("짧게라도 오늘의 감상을 남겨주세요!")
        else:
            with st.spinner("AI가 감상을 읽고 답장을 쓰고 있습니다..."):
                payload = {
                    "book_title": book["title"],
                    "read_pages": read_pages,
                    "user_thought": user_thought
                }
                log_res = requests.post(f"{API_BASE_URL}/daily-log", json=payload)
                
                if log_res.status_code == 200 and log_res.json().get("status") == "success":
                    st.balloons()
                    st.success("기록이 성공적으로 저장되었습니다!")
                else:
                    st.error("저장에 실패했습니다.")
    
    st.markdown("---")
    
    st.subheader("📚 나의 독서 기록 히스토리")
    past_logs = load_reading_logs(book["title"])
    
    if len(past_logs) == 0:
        st.caption("아직 작성된 기록이 없습니다. 첫 번째 기록을 남겨보세요!")
    else:
        latest_page = past_logs[0]['read_pages']
        progress = int((latest_page / book['page_count']) * 100)
        st.progress(progress / 100, text=f"완독까지 {progress}% 진행 중! ( {latest_page} / {book['page_count']} 쪽 )")
        
        # 💾 (NEW!) 마크다운 다운로드 버튼
        md_content = generate_markdown(book, curation, past_logs, st.session_state.user_goal)
        file_name = f"독서노트_{book['title'][:10]}.md"
        
        st.download_button(
            label="📄 마크다운(.md)으로 전체 노트 내보내기",
            data=md_content,
            file_name=file_name,
            mime="text/markdown",
            use_container_width=True
        )
        st.write("")
        
        for log in past_logs:
            date_str = log['created_at'][:16] 
            with st.expander(f"📅 {date_str} - {log['read_pages']}쪽까지 읽음"):
                st.write(f"**나의 감상:** {log['user_thought']}")
                st.info(f"🤖 **AI 메이트:** {log['ai_feedback']}")