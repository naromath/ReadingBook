import os
import requests
import json
import sqlite3 # 데이터베이스(DB) 라이브러리 추가
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

ALADIN_TTB_KEY = os.getenv("ALADIN_TTB_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ALADIN_TTB_KEY or not GEMINI_API_KEY:
    raise ValueError("API 키가 누락되었습니다. .env 파일을 확인해 주세요.")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# ==========================================
# 💾 데이터베이스 초기화 함수
# ==========================================
def init_db():
    # DB 파일(reading_habit.db)에 연결합니다. 없으면 새로 생성됩니다.
    conn = sqlite3.connect("reading_habit.db")
    cursor = conn.cursor()
    # 데일리 기록을 저장할 테이블을 만듭니다.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title TEXT,
            read_pages INTEGER,
            user_thought TEXT,
            ai_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 앱 실행 시 DB를 초기화합니다.
init_db()

# ==========================================
# 데이터 모델 정의
# ==========================================
class CurationRequest(BaseModel):
    user_goal: str
    book_title: str
    total_pages: int

class DailyLogRequest(BaseModel):
    book_title: str
    read_pages: int
    user_thought: str

# ==========================================
# API 엔드포인트
# ==========================================
@app.get("/")
def read_root():
    return {"status": "success", "message": "독서 습관 앱 백엔드 서버가 정상적으로 실행되었습니다!"}

@app.get("/api/books/{isbn}")
def get_book_info(isbn: str):
    url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={ALADIN_TTB_KEY}&itemIdType=ISBN13&ItemId={isbn}&output=js&Version=20131101"
    try:
        response = requests.get(url, timeout=5)
        clean_text = response.text.strip()
        if clean_text.endswith(";"):
            clean_text = clean_text[:-1]
            
        data = json.loads(clean_text)
        if "item" not in data or len(data["item"]) == 0:
            raise HTTPException(status_code=404, detail="해당 ISBN의 책을 찾을 수 없습니다.")
            
        book_info = data["item"][0]
        result = {
            "title": book_info.get("title", "제목 없음"),
            "authors": [book_info.get("author", "작자 미상")],
            "page_count": book_info.get("subInfo", {}).get("itemPage", 0), 
            "thumbnail": book_info.get("cover", "")
        }
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알라딘 API 통신 오류: {str(e)}")

@app.post("/api/curation")
def get_reading_schedule(request: CurationRequest):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        prompt = f"""
        당신은 전문적인 독서 큐레이터입니다.
        유저 목표: "{request.user_goal}"
        읽을 책: "{request.book_title}" (총 {request.total_pages}페이지)
        
        1주일(7일) 완독 계획을 짜주세요. 반드시 JSON 형식으로만 답변하세요.
        {{
            "curation_message": "이 책이 목표 달성에 어떻게 도움이 될지 동기부여 추천사",
            "daily_pages": 하루 권장 페이지 수 (정수형 숫자만),
            "schedule_advice": "독서 스케줄에 대한 실용적인 조언 1문장"
        }}
        """
        response = model.generate_content(prompt)
        result_text = response.text.replace("```json", "").replace("```", "").strip()
        return {"status": "success", "data": json.loads(result_text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 큐레이션 실패: {str(e)}")

@app.post("/api/daily-log")
def save_daily_log(request: DailyLogRequest):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        prompt = f"""
        당신은 유저의 독서 습관 형성을 돕는 다정한 페이스메이커입니다.
        유저가 오늘 '{request.book_title}' 책을 {request.read_pages}쪽까지 읽고 다음 감상을 남겼습니다: "{request.user_thought}"
        유저의 독서를 칭찬하고, 감상에 공감하며, 가벼운 질문을 하나 던져주세요. (2~3문장)
        """
        response = model.generate_content(prompt)
        ai_reply = response.text.strip()
        
        # 💾 AI 답변을 받은 후, DB에 유저의 기록과 AI의 피드백을 함께 저장합니다.
        conn = sqlite3.connect("reading_habit.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_logs (book_title, read_pages, user_thought, ai_feedback) 
            VALUES (?, ?, ?, ?)
        """, (request.book_title, request.read_pages, request.user_thought, ai_reply))
        conn.commit()
        conn.close()
        
        return {"status": "success", "data": {"ai_feedback": ai_reply}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 회고 및 저장 실패: {str(e)}")

# 💾 (NEW!) 특정 책의 모든 독서 기록을 DB에서 불러오는 API
@app.get("/api/logs/{book_title}")
def get_book_logs(book_title: str):
    try:
        conn = sqlite3.connect("reading_habit.db")
        conn.row_factory = sqlite3.Row # 컬럼명으로 데이터에 접근할 수 있게 해줌
        cursor = conn.cursor()
        
        # 최신 기록이 맨 위로 오도록 시간 역순(DESC)으로 정렬하여 가져옵니다.
        cursor.execute("SELECT * FROM daily_logs WHERE book_title = ? ORDER BY created_at DESC", (book_title,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"status": "success", "data": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기록 불러오기 실패: {str(e)}")