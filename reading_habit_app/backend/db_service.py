import sqlite3
import os

def get_db_connection():
    conn = sqlite3.connect("reading_habit.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect("reading_habit.db")
    cursor = conn.cursor()
    # 1. 기본 테이블 생성
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
    
    # 2. 마이그레이션: book_image 컬럼이 없으면 추가
    try:
        cursor.execute("ALTER TABLE daily_logs ADD COLUMN book_image TEXT")
    except sqlite3.OperationalError:
        # 이미 컬럼이 존재하는 경우 무시
        pass
        
    conn.commit()
    conn.close()

def save_log(book_title, read_pages, user_thought, ai_feedback, book_image=None):
    try:
        conn = sqlite3.connect("reading_habit.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO daily_logs (book_title, read_pages, user_thought, ai_feedback, book_image)
            VALUES (?, ?, ?, ?, ?)
        ''', (book_title, read_pages, user_thought, ai_feedback, book_image))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        return False

def get_logs(book_title=None):
    try:
        conn = sqlite3.connect("reading_habit.db")
        # 결과를 딕셔너리 형태로 받기 위해 row_factory 설정
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if book_title:
            cursor.execute("SELECT * FROM daily_logs WHERE book_title = ? ORDER BY created_at DESC", (book_title,))
        else:
            cursor.execute("SELECT * FROM daily_logs ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        # Row 객체를 딕셔너리 리스트로 변환
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return []

def get_unique_books():
    try:
        conn = sqlite3.connect("reading_habit.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # 제목별로 그룹화하여 가장 최신 이미지와 함께 가져옴
        cursor.execute('''
            SELECT book_title, book_image, MAX(created_at) as last_read 
            FROM daily_logs 
            GROUP BY book_title 
            ORDER BY last_read DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"DB 책 목록 조회 오류: {e}")
        return []
