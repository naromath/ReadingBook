import os
import requests
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_from_directory, jsonify
from dotenv import load_dotenv
from backend import db_service, ai_service, book_service  # 분리된 서비스들 임포트

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "reading-habit-secret-key-12345")

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# 서버 시작 시 DB 초기화
db_service.init_db()

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and origin in FRONTEND_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def api_options(path):
    return ("", 204)

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
    all_books = db_service.get_unique_books()
    return render_template("index.html", current_book=current_book, all_books=all_books)

@app.route("/scan")
def scan():
    return render_template("scan.html")

@app.route("/manifest.webmanifest")
def manifest():
    response = send_from_directory("static", "manifest.webmanifest")
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response

@app.route("/sw.js")
def service_worker():
    response = send_from_directory("static", "sw.js")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response

@app.route("/api/isbn/<isbn>", methods=["GET"])
def get_isbn_book_info(isbn):
    book_data = book_service.search_book_by_isbn(isbn)
    if not book_data:
        return {"status": "error", "message": "알라딘 API에서 해당 ISBN의 책을 찾지 못했습니다."}, 404
    return {"status": "success", "data": book_data}

@app.route("/api/v1/home", methods=["GET"])
def api_home():
    return jsonify({
        "status": "success",
        "data": {
            "current_book": session.get("book_data"),
            "all_books": db_service.get_unique_books()
        }
    })

@app.route("/api/v1/session", methods=["GET"])
def api_session():
    return jsonify({
        "status": "success",
        "data": {
            "book_data": session.get("book_data"),
            "curation_data": session.get("curation_data"),
            "user_goal": session.get("user_goal")
        }
    })

@app.route("/api/v1/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()
    requested_type = request.args.get("query_type", "Title")
    selected_query_type = requested_type if requested_type in ["Title", "Author", "ISBN13"] else "Title"

    if not query:
        return jsonify({"status": "error", "message": "검색어가 필요합니다."}), 400

    if selected_query_type == "Author":
        book_data = book_service.search_books(query, "Author")
    elif book_service.is_isbn(query) or selected_query_type == "ISBN13":
        selected_query_type = "ISBN13"
        book_data = book_service.search_book_by_isbn(query)
    else:
        book_data = book_service.search_books(query, "Title")

    if not book_data:
        return jsonify({"status": "error", "message": "책 정보를 찾지 못했습니다."}), 404

    session["book_data"] = book_data
    return jsonify({
        "status": "success",
        "data": {
            "book_data": book_data,
            "query": query,
            "query_type": selected_query_type
        }
    })

@app.route("/api/v1/register", methods=["POST"])
def api_register():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    query_type = (payload.get("query_type") or "Title").strip()
    user_goal = (payload.get("user_goal") or "").strip()

    if not query:
        return jsonify({"status": "error", "message": "검색어가 필요합니다."}), 400
    if not user_goal:
        return jsonify({"status": "error", "message": "독서 목적을 입력해 주세요."}), 400

    if query_type.upper() in ["ISBN", "ISBN13"]:
        book_data = book_service.search_book_by_isbn(query)
    else:
        book_data = book_service.search_books(query, query_type)

    if not book_data:
        return jsonify({"status": "error", "message": "책 정보를 찾을 수 없습니다."}), 404

    session["book_data"] = book_data
    session["user_goal"] = user_goal

    curation_data = ai_service.get_ai_curation(user_goal, book_data["title"], book_data["page_count"])
    if not curation_data:
        return jsonify({"status": "error", "message": "AI 큐레이션 생성에 실패했습니다."}), 500

    session["curation_data"] = curation_data
    return jsonify({
        "status": "success",
        "data": {
            "book_data": book_data,
            "curation_data": curation_data,
            "user_goal": user_goal
        }
    })

@app.route("/api/v1/log", methods=["POST"])
def api_log():
    payload = request.get_json(silent=True) or {}
    book_data = session.get("book_data")
    if not book_data:
        return jsonify({"status": "error", "message": "먼저 책을 등록해 주세요."}), 400

    read_pages = payload.get("read_pages")
    user_thought = (payload.get("user_thought") or "").strip()
    if read_pages is None or not user_thought:
        return jsonify({"status": "error", "message": "read_pages와 user_thought가 필요합니다."}), 400

    try:
        read_pages = int(read_pages)
    except ValueError:
        return jsonify({"status": "error", "message": "read_pages는 숫자여야 합니다."}), 400

    ai_reply = ai_service.get_ai_feedback(book_data["title"], read_pages, user_thought)
    book_image = book_data.get("thumbnail")
    saved = db_service.save_log(book_data["title"], read_pages, user_thought, ai_reply, book_image)
    if not saved:
        return jsonify({"status": "error", "message": "기록 저장에 실패했습니다."}), 500

    logs = db_service.get_logs(book_data["title"])
    return jsonify({
        "status": "success",
        "data": {
            "ai_feedback": ai_reply,
            "logs": logs
        }
    })

@app.route("/api/v1/bookshelf", methods=["GET"])
def api_bookshelf():
    book_data = session.get("book_data")
    logs = db_service.get_logs(book_data["title"]) if book_data else []
    all_books = db_service.get_unique_books()
    return jsonify({
        "status": "success",
        "data": {
            "book_data": book_data,
            "logs": logs,
            "all_books": all_books,
            "curation_data": session.get("curation_data")
        }
    })

@app.route("/search", methods=["GET", "POST"])
def search():
    # GET 요청 시 검색어(q)가 넘어오면 바로 처리 (스캔 결과 연결)
    if request.method == "GET" and request.args.get("q"):
        query = request.args.get("q", "").strip()
        requested_type = request.args.get("query_type", "Title")
        book_data = None
        selected_query_type = requested_type if requested_type in ["Title", "Author", "ISBN13"] else "Title"

        if selected_query_type == "Author":
            book_data = book_service.search_books(query, "Author")
        elif book_service.is_isbn(query) or selected_query_type == "ISBN13":
            selected_query_type = "ISBN13"
            book_data = book_service.search_book_by_isbn(query)
        else:
            book_data = book_service.search_books(query, "Title")

        if book_data:
            session['book_data'] = book_data
            return render_template(
                "search.html",
                auto_submit=True,
                scanned_book=book_data,
                query_value=query,
                selected_query_type=selected_query_type
            )
        flash("알라딘 API에서 책 정보를 찾지 못했습니다. ISBN 또는 제목을 확인해 주세요.", "error")
        return render_template("search.html", query_value=query, selected_query_type=selected_query_type)

    if request.method == "POST":
        query = (request.form.get("isbn") or "").strip()
        query_type = request.form.get("query_type", "Title")
        user_goal = request.form.get("user_goal")
        
        # 1. 책 정보 조회 (book_service 사용)
        if query_type.upper() in ["ISBN", "ISBN13"]:
            book_data = book_service.search_book_by_isbn(query)
        else:
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
            
    return render_template("search.html", query_value="", selected_query_type="Title")

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
