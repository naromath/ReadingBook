export type QueryType = 'Title' | 'Author' | 'ISBN13';

export interface BookData {
  title: string;
  authors: string[];
  page_count: number;
  thumbnail?: string;
  isbn13?: string;
  isbn?: string;
}

export interface CurationData {
  curation_message: string;
  daily_pages: number;
  schedule_advice: string;
}

export interface ReadingLog {
  id: number;
  book_title: string;
  read_pages: number;
  user_thought: string;
  ai_feedback: string;
  book_image?: string;
  created_at: string;
}

export interface BookshelfBook {
  book_title: string;
  book_image?: string;
  last_read?: string;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message?: string;
}
