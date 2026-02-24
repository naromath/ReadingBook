import os
import requests
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from dotenv import load_dotenv
from backend import db_service, ai_service, book_service  # 분리된 서비스들 임포트

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "reading-habit-secret-key-12345")

# 서버 시작 시 DB 초기화
db_service.init_db()

# --- 🛠 유틸리티 함수 ---
def generate_markdown_content(book, curation, logs, goal):
    md = "---\n"
    md += f"title: {book['title']}\n"
    md += f"author: {', '.join(book['authors'])}\n"
    md += f"total_pages: {book['page_count']}\n"
    md += "tags: [독서노트, Second_Brain]\n"
    md += "---\n\n"
    md += f"# 📚 {book['title']}\n\n"
    if book.get('thumbnail'):
        md += f"![Cover]({book['thumbnail']})\n\n"
    md += "## 🎯 나의 목표 및 AI 큐레이션\n"
    md += f"- **나의 목표**: {goal}\n"
    md += f"- **AI 추천사**: {curation['curation_message']}\n"
    md += f"- **독서 팁**: {curation['schedule_advice']}\n\n"
    md += "---\n\n"
    md += "## ✍️ 데일리 독서 기록\n\n"
    chronological_logs = reversed(logs)
    for log in chronological_logs:
        date_str = log['created_at'][:10]
        md += f"### 📅 {date_str} (p. {log['read_pages']})\n\n"
        md += f"**나의 감상:**\n> {log['user_thought']}\n\n"
        md += f"**🤖 AI 페이스메이커:**\n> {log['ai_feedback']}\n\n"
    return md

# --- 🛣 Flask Routes ---

@app.route("/")
def index():
    current_book = session.get('book_data')
    return render_template("index.html", current_book=current_book)

@app.route("/scan")
def scan():
    return render_template("scan.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    # GET 요청 시 검색어(q)가 넘어오면 바로 처리 (스캔 결과 연결)
    if request.method == "GET" and request.args.get("q"):
        query = request.args.get("q")
        book_data = book_service.get_book_info(query) # ISBN 대신 제목으로도 검색 가능하게 (내부 로직 확인 필요)
        if book_data:
            session['book_data'] = book_data
            return render_template("search.html", auto_submit=True)

    if request.method == "POST":
        query = request.form.get("isbn")
        query_type = request.form.get("query_type", "Title")
        user_goal = request.form.get("user_goal")
        
        # 1. 책 정보 조회 (book_service 사용)
        book_data = book_service.search_books(query, query_type)
        if not book_data:
            flash("책 정보를 찾을 수 없습니다. 정확한 ISBN 또는 제목을 확인해 주세요.", "error")
            return redirect(url_for("search"))
            
        session['book_data'] = book_data
        session['user_goal'] = user_goal
        
        # 2. AI 큐레이션 생성 (ai_service 사용)
        curation_data = ai_service.get_ai_curation(user_goal, book_data['title'], book_data['page_count'])
        if curation_data:
            session['curation_data'] = curation_data
            flash("새로운 책이 성공적으로 등록되었습니다!", "success")
            return redirect(url_for("log"))
        else:
            flash("AI 큐레이션 생성에 실패했습니다.", "error")
            return redirect(url_for("search"))
            
    return render_template("search.html")

@app.route("/analyze-cover", methods=["POST"])
def analyze_cover():
    data = request.json
    image_data = data.get("image")
    if not image_data:
        return {"status": "error", "message": "이미지 데이터가 없습니다."}
        
    # 이미지 분석 (ai_service 사용)
    result = ai_service.analyze_book_cover(image_data)
    if result:
        return {"status": "success", "data": result}
    else:
        return {"status": "error", "message": "책을 인식하지 못했습니다."}

@app.route("/log", methods=["GET", "POST"])
def log():
    book_data = session.get('book_data')
    curation_data = session.get('curation_data')
    
    if request.method == "POST":
        read_pages = int(request.form.get("read_pages"))
        user_thought = request.form.get("user_thought")
        
        # 1. AI 피드백 생성 (ai_service 사용)
        ai_reply = ai_service.get_ai_feedback(book_data['title'], read_pages, user_thought)
        
        # 2. 기록 저장 (db_service 사용)
        book_image = book_data.get('thumbnail')
        if db_service.save_log(book_data['title'], read_pages, user_thought, ai_reply, book_image):
            flash("오늘의 기록이 저장되었습니다! 👏", "success")
            return redirect(url_for("bookshelf"))
        else:
            flash("저장에 실패했습니다.", "error")
            
    return render_template("log.html", book_data=book_data, curation_data=curation_data)

@app.route("/bookshelf")
def bookshelf():
    book_data = session.get('book_data')
    logs = []
    if book_data:
        # 특정 책에 대한 기록 조회 (db_service 사용)
        logs = db_service.get_logs(book_data['title'])
    
    # 전체 책 리스트 조회
    all_books = db_service.get_unique_books()
    return render_template("bookshelf.html", book_data=book_data, logs=logs, all_books=all_books)

@app.route("/export")
def export():
    book_data = session.get('book_data')
    curation_data = session.get('curation_data')
    user_goal = session.get('user_goal')
    
    if not book_data: return redirect(url_for("index"))
    
    logs = db_service.get_logs(book_data['title'])
    content = generate_markdown_content(book_data, curation_data, logs, user_goal)
    
    return Response(content, mimetype="text/markdown",
                    headers={"Content-disposition": f"attachment; filename=reading_note_{book_data['title'][:10]}.md"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=True)
