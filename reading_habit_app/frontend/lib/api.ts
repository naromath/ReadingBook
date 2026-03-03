import type {
  ApiResponse,
  BookData,
  BookshelfBook,
  CurationData,
  QueryType,
  ReadingLog
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8501';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {})
    },
    credentials: 'include'
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = isJson && payload?.message ? payload.message : `요청 실패 (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return payload as T;
}

export async function getHome() {
  return apiRequest<ApiResponse<{ current_book: BookData | null; all_books: BookshelfBook[] }>>('/api/v1/home');
}

export async function getSession() {
  return apiRequest<ApiResponse<{ book_data: BookData | null; curation_data: CurationData | null; user_goal: string | null }>>('/api/v1/session');
}

export async function searchBook(query: string, queryType: QueryType) {
  const encodedQ = encodeURIComponent(query);
  const encodedType = encodeURIComponent(queryType);
  return apiRequest<ApiResponse<{ book_data: BookData; query: string; query_type: QueryType }>>(`/api/v1/search?q=${encodedQ}&query_type=${encodedType}`);
}

export async function registerBook(query: string, queryType: QueryType, userGoal: string) {
  return apiRequest<ApiResponse<{ book_data: BookData; curation_data: CurationData; user_goal: string }>>('/api/v1/register', {
    method: 'POST',
    body: JSON.stringify({ query, query_type: queryType, user_goal: userGoal })
  });
}

export async function getBookByIsbn(isbn: string) {
  return apiRequest<ApiResponse<BookData>>(`/api/isbn/${encodeURIComponent(isbn)}`);
}

export async function saveReadingLog(readPages: number, userThought: string) {
  return apiRequest<ApiResponse<{ ai_feedback: string; logs: ReadingLog[] }>>('/api/v1/log', {
    method: 'POST',
    body: JSON.stringify({ read_pages: readPages, user_thought: userThought })
  });
}

export async function getBookshelf() {
  return apiRequest<ApiResponse<{ book_data: BookData | null; logs: ReadingLog[]; all_books: BookshelfBook[]; curation_data: CurationData | null }>>('/api/v1/bookshelf');
}

export function getExportUrl() {
  return `${API_BASE_URL}/export`;
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}
