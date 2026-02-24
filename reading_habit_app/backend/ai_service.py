import os
import json
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # --- 🔍 가용 모델 확인 (디버깅용) ---
    print("\n--- [AI Service] 사용 가능한 Gemini 모델 목록 ---")
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                available_models.append(m.name)
    except Exception as e:
        print(f"모델 목록을 가져올 수 없습니다: {e}")
    print("--------------------------------------------\n")

# 기본적으로 사용할 모델 이름 (에러 방지를 위해 models/ 접두사 시도 또는 목록 기반 선택)
DEFAULT_MODEL = 'gemini-2.5-flash'

def get_ai_curation(user_goal, book_title, total_pages):
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        prompt = f"""
        전문적인 독서 큐레이터로서 JSON 형식으로만 답변하세요.
        유저 목표: "{user_goal}", 읽을 책: "{book_title}" ({total_pages}페이지)
        
        {{
            "curation_message": "추천사 (격려와 동기부여)",
            "daily_pages": 하루 권장 페이지 수 (정수),
            "schedule_advice": "독서 스케줄에 대한 실용적인 조언 1문장"
        }}
        """
        response = model.generate_content(prompt)
        text = response.text
        json_str = text[text.find("{"):text.rfind("}")+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"AI 큐레이션 오류: {e}")
        return None

def get_ai_feedback(book_title, read_pages, user_thought):
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        prompt = f"""
        당신은 다정한 독서 페이스메이커입니다. 2~3문장으로 답하세요.
        유저가 '{book_title}'을 {read_pages}쪽까지 읽고 남긴 감상: "{user_thought}"
        유저를 칭찬하고 감상에 공감하며, 다음 독서를 독려하는 가벼운 질문을 던져주세요.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI 피드백 오류: {e}")
        return "멋진 독서 기록이네요! 다음 기록도 기대할게요."

def analyze_book_cover(image_data):
    try:
        header, encoded = image_data.split(",", 1)
        image = Image.open(BytesIO(base64.b64decode(encoded)))
        
        model = genai.GenerativeModel(DEFAULT_MODEL)
        prompt = "이 책의 제목과 저자를 JSON으로 알려주세요: {\"title\": \"...\", \"author\": \"...\"}"
        response = model.generate_content([prompt, image])
        
        text = response.text
        json_str = text[text.find("{"):text.rfind("}")+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"이미지 분석 오류: {e}")
        return None
