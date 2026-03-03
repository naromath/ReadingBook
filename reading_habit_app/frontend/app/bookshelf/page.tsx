'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBaseUrl, getBookshelf, getExportUrl } from '@/lib/api';
import type { BookData, BookshelfBook, ReadingLog } from '@/types';

export default function BookshelfPage() {
  const router = useRouter();
  const [bookData, setBookData] = useState<BookData | null>(null);
  const [allBooks, setAllBooks] = useState<BookshelfBook[]>([]);
  const [logs, setLogs] = useState<ReadingLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        const response = await getBookshelf();
        setBookData(response.data.book_data);
        setAllBooks(response.data.all_books || []);
        setLogs(response.data.logs || []);
      } catch (e) {
        const message = e instanceof Error ? e.message : '책장 정보를 불러오지 못했습니다.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  const exportUrl = getExportUrl();
  const apiBase = getApiBaseUrl();

  return (
    <section className="content-card">
      <div className="section-row">
        <h1 className="hero-title small">My Bookshelf</h1>
        <a href={exportUrl} className="ghost-btn">Export .md</a>
      </div>

      {loading ? <p className="loading-text">책장을 불러오는 중...</p> : null}
      {error ? <div className="message-box error">{error}</div> : null}

      <div className="book-row compact-row">
        {allBooks.length > 0 ? (
          allBooks.map((book) => (
            <article className="book-tile mini" key={`${book.book_title}-${book.last_read || ''}`}>
              <div className="cover-slot small">
                {book.book_image ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img className="cover-img" src={book.book_image} alt={book.book_title} />
                ) : (
                  <div className="no-cover">NO COVER</div>
                )}
              </div>
              <h3>{book.book_title}</h3>
            </article>
          ))
        ) : (
          <div className="status-panel">아직 등록된 책이 없습니다.</div>
        )}
      </div>

      <div className="section-row inner-space">
        <h2>Reading History</h2>
        <button type="button" className="ghost-btn" onClick={() => router.push('/log')}>Write Log</button>
      </div>

      {!loading && !bookData ? (
        <div className="status-panel warning">
          현재 등록된 독서 세션이 없습니다. <button type="button" className="ghost-btn" onClick={() => router.push('/search')}>책 등록</button>
        </div>
      ) : null}

      {logs.length === 0 ? (
        <div className="status-panel">선택된 책의 기록이 없습니다. 먼저 독서 기록을 남겨보세요.</div>
      ) : (
        logs.map((log) => (
          <article className="history-item" key={log.id}>
            <div className="history-head">
              <span>{log.created_at.slice(0, 16)}</span>
              <span>{log.read_pages}쪽</span>
            </div>
            <div className="history-body">
              <p><strong>내 감상</strong></p>
              <blockquote>{log.user_thought}</blockquote>
              <p><strong>AI 메이트</strong></p>
              <p>{log.ai_feedback}</p>
            </div>
          </article>
        ))
      )}

      <p className="muted-copy" style={{ marginTop: 10 }}>
        세션 기반 내보내기는 Flask 서버({apiBase})의 <code>/export</code> 엔드포인트를 사용합니다.
      </p>
    </section>
  );
}
