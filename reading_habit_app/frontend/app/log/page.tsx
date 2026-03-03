'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSession, saveReadingLog } from '@/lib/api';
import type { BookData, CurationData } from '@/types';

export default function LogPage() {
  const router = useRouter();
  const [bookData, setBookData] = useState<BookData | null>(null);
  const [curationData, setCurationData] = useState<CurationData | null>(null);
  const [readPages, setReadPages] = useState<number>(1);
  const [userThought, setUserThought] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        const response = await getSession();
        setBookData(response.data.book_data);
        setCurationData(response.data.curation_data);
      } catch (e) {
        const messageText = e instanceof Error ? e.message : '세션 정보를 불러오지 못했습니다.';
        setError(messageText);
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  useEffect(() => {
    if (curationData?.daily_pages) {
      setReadPages(curationData.daily_pages);
    }
  }, [curationData]);

  const maxPages = useMemo(() => bookData?.page_count || 1, [bookData]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!bookData) {
      setError('먼저 책을 등록해 주세요.');
      return;
    }
    if (!userThought.trim()) {
      setError('인상 깊었던 점을 입력해 주세요.');
      return;
    }

    setSaving(true);
    setMessage('');
    setError('');

    try {
      const response = await saveReadingLog(readPages, userThought.trim());
      setMessage(`저장 완료: ${response.data.ai_feedback}`);
      router.push('/bookshelf');
    } catch (e) {
      const messageText = e instanceof Error ? e.message : '기록 저장에 실패했습니다.';
      setError(messageText);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="content-card">
      <div className="section-row">
        <h1 className="hero-title small">Reading Log</h1>
        <button type="button" className="ghost-btn" onClick={() => router.push('/bookshelf')}>My Shelf</button>
      </div>

      {loading ? <p className="loading-text">세션 정보를 불러오는 중...</p> : null}
      {message ? <div className="message-box">{message}</div> : null}
      {error ? <div className="message-box error">{error}</div> : null}

      {!loading && !bookData ? (
        <div className="status-panel warning">
          먼저 <button type="button" className="ghost-btn" onClick={() => router.push('/search')}>새로운 책 저장</button>에서 읽을 책을 등록해 주세요.
        </div>
      ) : null}

      {bookData ? (
        <>
          <article className="result-card">
            {bookData.thumbnail ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={bookData.thumbnail} className="result-cover" alt={bookData.title} />
            ) : null}
            <div>
              <h3>{bookData.title}</h3>
              <p>{bookData.authors?.[0] || '저자 정보 없음'}</p>
              <p className="muted-copy">총 {bookData.page_count}쪽</p>
              {curationData ? <p className="muted-copy"><strong>AI 큐레이터:</strong> {curationData.curation_message}</p> : null}
            </div>
          </article>

          <form onSubmit={onSubmit} className="stack-form">
            <div className="form-grid two">
              <div>
                <label htmlFor="readPages" className="label">오늘 누적 읽은 쪽수</label>
                <input
                  id="readPages"
                  type="number"
                  min={1}
                  max={maxPages}
                  value={readPages}
                  onChange={(event) => setReadPages(Number(event.target.value))}
                  required
                />
                <p className="muted-copy">전체 {maxPages}쪽</p>
              </div>
              <div>
                <label htmlFor="thought" className="label">인상 깊었던 점</label>
                <textarea
                  id="thought"
                  rows={5}
                  value={userThought}
                  onChange={(event) => setUserThought(event.target.value)}
                  placeholder="오늘 읽은 부분에서 무엇을 느꼈나요?"
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn-primary-solid" disabled={saving}>
              {saving ? '저장 중...' : '기록 저장 및 AI 피드백 받기'}
            </button>
          </form>
        </>
      ) : null}
    </section>
  );
}
