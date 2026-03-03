import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
ALADIN_TTB_KEY = os.getenv("ALADIN_TTB_KEY")

def normalize_isbn(value):
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit() or ch in ("X", "x")).upper()

def is_isbn(value):
    isbn = normalize_isbn(value)
    return len(isbn) in (10, 13)

def search_books(query, query_type='Keyword'):
    """
    알라딘 API를 사용하여 책을 검색합니다.
    query_type: 'Title', 'Author', 'ISBN' (또는 'ISBN13'), 'Keyword'
    """
    # ISBN인 경우 ItemLookUp API 사용
    if query_type.upper() in ['ISBN', 'ISBN13']:
        normalized_query = normalize_isbn(query)
        if not normalized_query:
            return None
        url = f"http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx?ttbkey={ALADIN_TTB_KEY}&itemIdType={query_type}&ItemId={normalized_query}&output=js&Version=20131101"
    else:
        # 제목, 저자 등은 ItemSearch API 사용
        url = f"http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?ttbkey={ALADIN_TTB_KEY}&Query={query}&QueryType={query_type}&MaxResults=1&start=1&SearchTarget=Book&output=js&Version=20131101"

    try:
        response = requests.get(url, timeout=5)
        clean_text = response.text.strip()
        if clean_text.endswith(";"):
            clean_text = clean_text[:-1]
            
        data = json.loads(clean_text)
        items = data.get("item", [])
        if not items:
            return None
            
        book_info = items[0]
        return {
            "title": book_info.get("title", "제목 없음"),
            "authors": [book_info.get("author", "작자 미상")],
            "page_count": book_info.get("subInfo", {}).get("itemPage", 200), 
            "thumbnail": book_info.get("cover", ""),
            "isbn13": book_info.get("isbn13", ""),
            "isbn": book_info.get("isbn", "")
        }
    except Exception as e:
        print(f"알라딘 API 오류: {e}")
        return None

def search_book_by_isbn(identifier):
    isbn = normalize_isbn(identifier)
    if not isbn:
        return None

    if len(isbn) == 13:
        return search_books(isbn, 'ISBN13') or search_books(isbn, 'ISBN')
    if len(isbn) == 10:
        return search_books(isbn, 'ISBN') or search_books(isbn, 'ISBN13')
    return search_books(isbn, 'ISBN13') or search_books(isbn, 'ISBN')

# 기존 코드와의 호환성을 위해 유지 (내부적으로 search_books 호출)
def get_book_info(identifier):
    return search_book_by_isbn(identifier)
